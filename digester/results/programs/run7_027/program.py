from smoothstep_interpolate import smoothstep_interpolate
from anti_windup_pi_step import anti_windup_pi_step

SUBGOAL = "plateau_40"

_KNOTS = (
    (4.9, 255.0),
    (6.2, 200.0),
    (7.4, 190.0),
    (8.3, 152.0),
    (9.2, 142.0),
)

_SETPOINT = 0.55
_KP = 150.0
_KI = 5.0
_KD = 200.0
_MIN_FEED = 90.0
_MAX_FEED = 255.0

_CLIMB_STEP = 12.0
_VFA_CLIMB_LIMIT = 0.70
_RISE_CLIMB_LIMIT = 0.05
_EMERGENCY_VFA_LIMIT = 0.85


def _clamp(value):
    return max(_MIN_FEED, min(_MAX_FEED, value))


def act(observation: dict, memory: dict) -> tuple[list[float], str]:
    completed = int(round(float(observation["day"]) * 4.0))
    decision = completed + 1

    if completed == 0 or "handoff_state" not in memory:
        memory["handoff_state"] = {
            "ch4": [],
            "last_assay_step": None,
            "previous_vfa": None,
            "integral": 0.0,
        }
    state = memory["handoff_state"]
    state["ch4"].append(float(observation["ch4_flow"]))

    # Only process newly delivered assays; zero placeholders are ignored.
    fresh_assay = (
        int(observation["assay_age"]) == 0
        and completed >= 4
        and state["last_assay_step"] != completed
    )
    if fresh_assay:
        total_vfa = sum(
            max(0.0, float(observation[name]))
            for name in ("vfa_s_va", "vfa_s_bu", "vfa_s_pro", "vfa_s_ac")
        )
        previous_vfa = state["previous_vfa"]
        previous_step = state["last_assay_step"]
        state["previous_vfa"] = total_vfa
        state["last_assay_step"] = completed

    # Preserve the original maximum-command probe and draw classifier.
    if decision <= 3:
        return [255.0], SUBGOAL

    if "plateau" not in state:
        history = state["ch4"]
        ch4_start = 0.5 * (history[0] + 1650.0)
        gain = (history[3] - ch4_start) / 68.0
        state["plateau"] = _clamp(float(smoothstep_interpolate(gain, _KNOTS)))
        state["command"] = state["plateau"]

    if decision < 8:
        return [state["command"]], SUBGOAL

    if "controller_started" not in state:
        state["controller_started"] = True
        state["integral"] = 0.0
        state["step_size"] = _CLIMB_STEP
        state["backed_off"] = False
        state["freeze_until"] = 0
        state["assays_since_climb"] = 0

        if fresh_assay:
            interval_days = (
                (completed - previous_step) * 0.25
                if previous_step is not None else 1.0
            )
            error = _SETPOINT - total_vfa
            rise_per_day = (
                max(0.0, (total_vfa - previous_vfa) / interval_days)
                if previous_vfa is not None else 0.0
            )
            proportional = _KP * error
            derivative = -_KD * rise_per_day
            increment = _KI * error * interval_days

            pi_cmd, integral = anti_windup_pi_step(
                state["plateau"],
                proportional,
                state["integral"],
                increment,
                derivative,
                _MIN_FEED,
                _MAX_FEED,
            )
            state["integral"] = integral
            # Hand off to attempt 19's PI output at decision 8 if safe, else class plateau
            if total_vfa < _VFA_CLIMB_LIMIT and rise_per_day < _RISE_CLIMB_LIMIT:
                state["base_feed"] = max(state["plateau"], pi_cmd)
            else:
                state["base_feed"] = pi_cmd
        else:
            state["base_feed"] = state["plateau"]

        state["command"] = state["base_feed"]
        return [float(state["command"])], SUBGOAL

    if fresh_assay:
        interval_days = (
            (completed - previous_step) * 0.25
            if previous_step is not None else 1.0
        )
        vfa_rise = (
            total_vfa - previous_vfa
            if previous_vfa is not None else 0.0
        )
        rise_per_day = max(0.0, vfa_rise / interval_days)

        violates_climb = (
            total_vfa >= _VFA_CLIMB_LIMIT or vfa_rise >= _RISE_CLIMB_LIMIT
        )

        if violates_climb and not state["backed_off"]:
            state["base_feed"] = _clamp(
                state["base_feed"] - 2.0 * state["step_size"]
            )
            state["backed_off"] = True
            state["freeze_until"] = completed + 16
            state["step_size"] = 0.5 * _CLIMB_STEP
            state["assays_since_climb"] = 0
        elif completed >= state["freeze_until"]:
            if not violates_climb:
                state["assays_since_climb"] += 1
                if state["assays_since_climb"] >= 2:
                    state["base_feed"] = _clamp(
                        state["base_feed"] + state["step_size"]
                    )
                    state["assays_since_climb"] = 0
            else:
                state["assays_since_climb"] = 0

        # Emergency derivative brake and PI cut whenever an assay is above 0.85
        if total_vfa > _EMERGENCY_VFA_LIMIT:
            error = _SETPOINT - total_vfa
            proportional = _KP * error
            derivative = -_KD * rise_per_day
            increment = _KI * error * interval_days
            cmd, integral = anti_windup_pi_step(
                state["base_feed"],
                proportional,
                state["integral"],
                increment,
                derivative,
                _MIN_FEED,
                _MAX_FEED,
            )
            state["integral"] = integral
            state["command"] = cmd
            state["base_feed"] = min(state["base_feed"], cmd)
            state["freeze_until"] = max(state["freeze_until"], completed + 16)
            state["assays_since_climb"] = 0
        else:
            state["command"] = state["base_feed"]

    return [float(state["command"])], SUBGOAL
