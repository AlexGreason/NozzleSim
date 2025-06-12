import math
import helperfuncs as h


def manual_prop_angle(gamma, v1, theta, delta):
    """Return expected propagation angle of a characteristic after a bend."""
    M1 = h.calcmach(gamma, 1, v1)
    v2 = v1 + abs(delta)
    M2 = h.calcmach(gamma, 1, v2)
    mu1 = math.degrees(math.asin(1 / M1))
    mu2 = math.degrees(math.asin(1 / M2))
    theta1 = theta
    theta2 = theta + delta
    sign = 1 if delta < 0 else -1
    return (theta1 + theta2) / 2 + sign * (mu1 + mu2) / 2


def run_cases():
    cases = [
        dict(gamma=1.4, M1=2.0, theta=0.0, delta=-5.0),
        dict(gamma=1.4, M1=3.0, theta=0.0, delta=10.0),
        dict(gamma=1.4, M1=2.0, theta=15.0, delta=-3.0),
    ]
    for i, case in enumerate(cases, 1):
        gamma = case['gamma']
        v1 = h.calcv(gamma, 1, case['M1'])
        theta = case['theta']
        delta = case['delta']
        code_angle = h.shockprop(gamma, v1, theta, delta)
        manual_angle = manual_prop_angle(gamma, v1, theta, delta)
        diff = code_angle - manual_angle
        print(f"Case {i}: gamma={gamma}, M1={case['M1']}, theta={theta}, delta={delta}")
        print(f"  computed: {code_angle:.6f}")
        print(f"  manual:   {manual_angle:.6f}")
        print(f"  diff:     {diff:.6g}\n")


if __name__ == '__main__':
    run_cases()
