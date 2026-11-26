from soft_control_loop.programs import skill


@skill
def startup_vfa_wave_done(memory, vfa_total, new_lab, min_peak=0.6, drop=0.75):
    """Return True once the startup VFA wave has peaked and receded.

    memory: the program's own memory dict; the skill keeps the keys
        'startup_vfa_peak' and 'startup_vfa_done' in it.
    vfa_total: total lab VFA (same units as the thresholds), or None when
        the lab has given no value.
    new_lab: True only on the step a fresh lab reading arrives.
    min_peak: smallest peak that counts as a real startup wave.
    drop: fraction of the peak below which the wave counts as over.

    During startup, acids rise sharply and then fall as methanogens grow.
    VFA-based limit triggers that fire on that wave latch the load far
    too early. Until this returns True, such triggers should stay off.
    Once True it stays True.
    """
    if "startup_vfa_peak" not in memory:
        memory["startup_vfa_peak"] = 0.0
        memory["startup_vfa_done"] = False
    if new_lab and vfa_total is not None:
        if vfa_total > memory["startup_vfa_peak"]:
            memory["startup_vfa_peak"] = vfa_total
        elif (
            memory["startup_vfa_peak"] > min_peak
            and vfa_total < drop * memory["startup_vfa_peak"]
        ):
            memory["startup_vfa_done"] = True
    return memory["startup_vfa_done"]
