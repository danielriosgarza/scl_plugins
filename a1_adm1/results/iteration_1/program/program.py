from ewma_update import ewma_update


def _clip(value, low, high):
    return max(low, min(high, value))


def _pump(previous, target, slew, maximum):
    return float(_clip(target, max(0.0, previous - slew), min(maximum, previous + slew)))


def act(observation, memory):
    sludge = memory.get('last_sludge', 85.0)
    carb = memory.get('last_carb', 0.0)
    methane = max(0.0, float(observation['ch4_flow']))
    total_gas = methane + max(0.0, float(observation['co2_flow']))
    if total_gas > 0.0:
        reading = methane / total_gas
        memory.setdefault('initial_fraction', reading)
    else:
        reading = memory.get('fraction', 0.63)

    floor = _clip(memory.get('initial_fraction', 0.63) - 0.135, 0.498, 0.508)
    fraction, fraction_change = ewma_update(memory, 'fraction', reading, 0.36)
    pressure, pressure_change = ewma_update(memory, 'pressure', float(observation['ch4_pressure']), 0.33)
    flow, flow_change = ewma_update(memory, 'methane', methane, 0.25)
    ph, _ = ewma_update(memory, 'ph', float(observation['ph']), 0.25)
    window = memory.get('fraction_window', [fraction] * 8)[1:] + [fraction]
    memory['fraction_window'] = window

    acids = [observation.get(key) for key in ('vfa_s_va', 'vfa_s_bu', 'vfa_s_pro', 'vfa_s_ac')]
    vfa = None if any(value is None for value in acids) else 1000.0 * sum(acids)
    done = memory.setdefault('startup_done', False)
    acid_veto = vfa is not None and vfa > (0.8 if done else 2.5)
    gas_alarm = fraction < floor - 0.012 or (
        fraction < floor + 0.003 and fraction_change < -0.004 and pressure_change < -0.003
    )
    acid_alarm = acid_veto and (ph < 6.76 or fraction < floor or done)
    alarm = gas_alarm or acid_alarm or ph < 6.58
    hold = (total_gas <= 0.0 or fraction < floor or fraction_change < -0.009 or acid_veto)

    sludge_target, carb_target = sludge, carb
    if alarm:
        # A new lab result may justify another cut. Between samples the gas meters stay live.
        if gas_alarm or ph < 6.58 or observation.get('lab_age') == 4:
            carb_target = carb - 10.0
        if ph < 6.65 and acid_veto:
            sludge_target = min(sludge, 200.0)
    elif not done and not hold:
        # Advance beyond the initial loading plateau only when gas production has responded.
        settled = (flow > 5900.0 and abs(flow_change) < 180.0 and pressure > 0.61
                   and fraction >= floor + 0.004 and vfa is not None and vfa < 1.0)
        expanded = memory.get('expanded', False) or settled
        memory['expanded'] = expanded
        sludge_target = min(sludge + (5.0 if sludge >= 200.0 else 34.0), 270.0 if expanded else 210.0)
        if expanded:
            carb_cap = 105.0 + _clip((fraction - floor - 0.009) * 320.0, 0.0, 7.0)
        else:
            carb_cap = 90.0
        increment = 10.0
        if carb >= 85.0:
            increment = 2.0
        elif flow_change > 150.0 or fraction_change < -0.004:
            increment = 5.0
        carb_target = min(carb + increment, carb_cap)

        if (expanded and sludge >= 270.0 and carb >= carb_cap - 1.0 and settled
                and max(window) - min(window) < 0.012):
            memory['startup_done'] = True
            sludge_target, carb_target = sludge, carb

    sludge = _pump(sludge, sludge_target, 34.0, 1000.0)
    carb = _pump(carb, carb_target, 10.0, 300.0)
    memory['last_sludge'], memory['last_carb'] = sludge, carb
    return [sludge, carb], 'ramp_up'
