from math import sqrt, exp, log

global N1, I1, J1  # I phase
global N02, J02, Nr2, Ir2, Jr2  # II phase
global N02m, Nr2m, Ir2m, Jr2m  # metastable-vapor region
global N3, I3, J3  # III phase
global N05, J05, Nr5, Ir5, Jr5  # V phase
global Vi0, VHi, Vi, Vj, VHij  # Viscosity
non, dt, dtt, dtp, dp, dpp = 0, 1, 2, 3, 4, 5  # Триггеры функции энергии Гиббса
R, Default_accuracy = 461.526, 3

N1 = [0.14632971213167, -0.84548187169114, -3.756360367204, 3.3855169168385, -0.95791963387872, 0.15772038513228,
      -0.016616417199501, 8.1214629983568E-04, 2.8319080123804E-04, -6.0706301565874E-04, -0.018990068218419,
      -0.032529748770505, -0.021841717175414, -5.283835796993E-05, -4.7184321073267E-04, -3.0001780793026E-04,
      4.7661393906987E-05, -4.4141845330846E-06, -7.2694996297594E-16, -3.1679644845054E-05, -2.8270797985312E-06,
      -8.5205128120103E-10, -2.2425281908E-06, -6.5171222895601E-07, -1.4341729937924E-13, -4.0516996860117E-07,
      -1.2734301741641E-09, -1.7424871230634E-10, -6.8762131295531E-19, 1.4478307828521E-20, 2.6335781662795E-23,
      -1.1947622640071E-23, 1.8228094581404E-24, -9.3537087292458E-26]
I1 = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 8, 8, 21, 23, 29, 30, 31, 32]
J1 = [-2, -1, 0, 1, 2, 3, 4, 5, -9, -7, -1, 0, 1, 3, -3, 0, 1, 3, 17, -4, 0, 6, -5, -2, 10, -8, -11, -6, -29, -31, -38,
      -39, -40, -41]
N02 = [-9.6927686500217, 10.086655968018, -0.005608791128302, 0.071452738081455, -0.40710498223928, 1.4240819171444,
       -4.383951131945, -0.28408632460772, 0.021268463753307]
N02m = [-9.6937268393049, 10.087275970006, -0.005608791128302, 0.071452738081455, -0.40710498223928, 1.4240819171444,
        -4.383951131945, -0.28408632460772, 0.021268463753307]
J02 = [0, 1, -5, -4, -3, -2, -1, 2, 3]
Nr2 = [-1.7731742473213E-03, -0.017834862292358, -0.045996013696365, -0.057581259083432, -0.05032527872793,
       -3.3032641670203E-05, -1.8948987516315E-04, -3.9392777243355E-03, -0.043797295650573, -2.6674547914087E-05,
       2.0481737692309E-08, 4.3870667284435E-07, -3.227767723857E-05, -1.5033924542148E-03, -0.040668253562649,
       -7.8847309559367E-10, 1.2790717852285E-08, 4.8225372718507E-07, 2.2922076337661E-06, -1.6714766451061E-11,
       -2.1171472321355E-03, -23.895741934104, -5.905956432427E-18, -1.2621808899101E-06, -0.038946842435739,
       1.1256211360459E-11, -0.082311340897998, 1.9809712802088E-08, 1.0406965210174E-19, -1.0234747095929E-13,
       -1.0018179379511E-09, -8.0882908646985E-11, 0.10693031879409, -0.33662250574171, 8.9185845355421E-25,
       3.0629316876232E-13, -4.2002467698208E-06, -5.9056029685639E-26, 3.7826947613457E-06, -1.2768608934681E-15,
       7.3087610595061E-29, 5.5414715350778E-17, -9.436970724121E-07]
Ir2 = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 5, 6, 6, 6, 7, 7, 7, 8, 8, 9, 10, 10, 10, 16, 16, 18, 20,
       20, 20, 21, 22, 23, 24, 24, 24]
Jr2 = [0, 1, 2, 3, 6, 1, 2, 4, 7, 36, 0, 1, 3, 6, 35, 1, 2, 3, 7, 3, 16, 35, 0, 11, 25, 8, 36, 13, 4, 10, 14, 29, 50,
       57, 20, 35, 48, 21, 53, 39, 26, 40, 58]
Nr2m = [-7.3362260186506E-03, -0.088223831943146, -0.072334555213245, -4.0813178534455E-03, 2.0097803380207E-03,
        -0.053045921898642, -0.007619040908697, -6.3498037657313E-03, -0.086043093028588, 0.007532158152277,
        -7.9238375446139E-03, -2.2888160778447E-04, -0.002645650148281]
Ir2m = [1, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5, 5]
Jr2m = [0, 2, 5, 11, 1, 7, 16, 4, 16, 7, 10, 9, 10]
N3 = [-15.732845290239, 20.944396974307, -7.6867707878716, 2.6185947787954, -2.808078114862, 1.2053369696517,
      -8.4566812812502E-03, -1.2654315477714, -1.1524407806681, 0.88521043984318, -0.64207765181607, 0.38493460186671,
      -0.85214708824206, 4.8972281541877, -3.0502617256965, 0.039420536879154, 0.12558408424308, -0.2799932969871,
      1.389979956946, -2.018991502357, -8.2147637173963E-03, -0.47596035734923, 0.0439840744735, -0.44476435428739,
      0.90572070719733, 0.70522450087967, 0.10770512626332, -0.32913623258954, -0.50871062041158, -0.022175400873096,
      0.094260751665092, 0.16436278447961, -0.013503372241348, -0.014834345352472, 5.7922953628084E-04,
      3.2308904703711E-03, 8.0964802996215E-05, -1.6557679795037E-04, -4.4923899061815E-05]
I3 = [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 6, 6, 6, 7, 8, 9, 9, 10,
      10, 11]
J3 = [0, 1, 2, 7, 10, 12, 23, 2, 6, 15, 17, 0, 2, 6, 7, 22, 26, 0, 2, 4, 16, 26, 0, 2, 4, 26, 1, 3, 26, 0, 2, 26, 2, 26,
      2, 26, 0, 1, 26]
N05 = [-13.179983674201, 6.8540841634434, -0.024805148933466, 0.36901534980333, -3.1161318213925, -0.32961626538917]
J05 = [0, 1, -3, -2, -1, 2]
Nr5 = [1.5736404855259E-03, 9.0153761673944E-04, -5.0270077677648E-03, 2.2440037409485E-06, -4.1163275453471E-06,
       3.7919454822955E-08]
Ir5 = [1, 1, 1, 2, 2, 3]
Jr5 = [1, 2, 3, 3, 9, 7]
VHi = [1.67752, 2.20462, 0.6366564, -0.241605]
Vi = [0, 1, 2, 3, 0, 1, 2, 3, 5, 0, 1, 2, 3, 4, 0, 1, 0, 3, 4, 3, 5]
Vj = [0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 4, 4, 5, 6, 6]
VHij = [0.520094, 0.0850895, -1.08374, -0.289555, 0.222531, 0.999115, 1.88797, 1.26613, 0.120573, -0.281378, -0.906851,
        -0.772479, -0.489837, -0.25704, 0.161913, 0.257399, -0.0325372, 0.0698452, 0.00872102, -0.00435673,
        -0.000593264]


def N_Update():
    N1, n2, N3, n4 = 1167.0521452767, -724213.16703206, -17.073846940092, 12020.82470247
    n5, n6, n7, n8 = -3232555.0322333, 14.91510861353, -4823.2657361591, 405113.40542057
    n9, n10 = -0.23855557567849, 650.17534844798
    return N1, n2, N3, n4, n5, n6, n7, n8, n9, n10


def Region(t: float, p: float) -> int:
    if (t <= 590) and (p <= 100):
        pf = Border_Pressure(t)
    ans = 0
    if (590 < t) and (t <= 800) and (0 <= p) and (p <= 100):
        ans = 2
    elif (800 < t) and (t <= 2000) and (0 <= p) and (p <= 50):
        ans = 5
    elif (0 <= t) and (t <= 350) and (pf < p) and (p <= 100):
        ans = 1
    elif (350 < t) and (t <= 590) and (pf < p) and (p <= 100):
        ans = 3
    elif (0 <= t) and (t <= 590) and (0 <= p) and (p < pf):
        ans = 2
    elif (0 <= t) and (t <= 590) and (p == pf):
        ans = 4
    return ans


def Density3(t: float, p: float, accuracy=None) -> float:
    if t < 373.946:
        if Saturation_Pressure(t) < p:
            ro_min = 322
            ro_max = 762.4
        else:
            ro_min = 113.6
            ro_max = 322
    else:
        ro_min = 113.6
        ro_max = 762.4

    ro_mid = (ro_max + ro_min) / 2
    p_mid = ro_mid ** 2 * R * (t + 273.15) * JF(t, ro_mid, dp, 3) / 322000000 - p
    faccuracy = 10 ** (-Default_accuracy) if accuracy is None else 10 ** (-accuracy)

    while (abs(p_mid) > faccuracy) and (abs(ro_max - ro_mid) > faccuracy):
        if p_mid < 0:
            ro_min = ro_mid
        else:
            ro_max = ro_mid
        ro_mid = (ro_max + ro_min) / 2
        p_mid = ro_mid ** 2 * R * (t + 273.15) * JF(t, ro_mid, dp, 3) / 322000000 - p

    ans = 1 / 0 if abs(p_mid) > faccuracy else ro_mid
    return ans


def Helmholtz_Energy(t: float, ro: float) -> float:
    return JF(t, ro, non, 3) * (t + 273.15) * R


def Pressure3(t: float, ro: float) -> float:
    return ro ** 2 * R * (t + 273.15) * JF(t, ro, dp, 3) / 322


def Specific_Energy3(t: float, ro: float) -> float:
    return R * 647.096 * JF(t, ro, dt, 3)


def Specific_Entropy3(t: float, ro: float) -> float:
    return R * (647.096 / (t + 273.15) * JF(t, ro, dt, 3) - JF(t, ro, non, 3))


def Specific_Entalpy3(t: float, ro: float) -> float:
    return R * (647.096 * JF(t, ro, dt, 3) + (t + 273.15) * JF(t, ro, dp, 3) * ro / 322)


def Heat_Isobary3(t: float, ro: float) -> float:
    tf = 647.096 / (t + 273.15)
    rof = ro / 322
    fp = JF(t, ro, dp, 3)
    return (-tf ** 2 * JF(t, ro, dtt, 3) + (fp - tf * JF(t, ro, dtp, 3)) ** 2 / (2 * fp / rof + JF(t, ro, dpp, 3))) * R


def Heat_Isochorny3(t: float, ro: float) -> float:
    return -(647.096 / (t + 273.15)) ** 2 * JF(t, ro, dtt, 3) * R


def Sound_Speed3(t: float, ro: float) -> float:
    tf = 647.096 / (t + 273.15)
    rof = ro / 322
    fp = JF(t, ro, dp, 3)
    return (R * (t + 273.15) * rof ** 2 * (2 * fp / rof + JF(t, ro, dpp, 3) - (fp - tf * JF(t, ro, dtp, 3)) ** 2 / (
            tf ** 2 * JF(t, ro, dtt, 3)))) ** 0.5


def Gibbs_Energy(t: float, p: float, reg=None) -> float:
    Trigger = Region(t, p) if reg is None else reg

    if Trigger in [1, 2, 4, 5, 21]:
        return JF(t, p, non, Trigger) * (t + 273.15) * R
    elif Trigger == 3:
        ro = Density3(t, p)
        return JF(t, ro, non, 3) * (t + 273.15) * R


def Specific_Volume(t: float, p: float, reg=None) -> float:
    Trigger = Region(t, p) if reg is None else reg

    if Trigger == 1:
        return (t + 273.15) * R * JF(t, p, dp, Trigger) / 16530000
    elif Trigger in [2, 4, 5, 21]:
        return (t + 273.15) * R * JF(t, p, dp, Trigger) / 1000000
    elif Trigger == 3:
        return 1 / Density3(t, p)


def Density(t: float, p: float, reg=None) -> float:
    Trigger = Region(t, p) if reg is None else reg

    if Trigger == 1:
        return 1 / ((t + 273.15) * R * JF(t, p, dp, Trigger) / 16530000)
    elif Trigger in [2, 4, 5, 21]:
        return 1 / ((t + 273.15) * R * JF(t, p, dp, Trigger) / 1000000)
    elif Trigger == 3:
        return Density3(t, p)


def Specific_Energy(t: float, p: float, reg=None) -> float:
    Trigger = Region(t, p) if reg is None else reg

    if Trigger == 1:
        return R * (1386 * JF(t, p, dt, Trigger) - p / 16.53 * (t + 273.15) * JF(t, p, dp, Trigger))
    elif Trigger in [2, 4, 21]:
        return R * (540 * JF(t, p, dt, Trigger) - p * (t + 273.15) * JF(t, p, dp, Trigger))
    elif Trigger == 5:
        return R * (1000 * JF(t, p, dt, Trigger) - p * (t + 273.15) * JF(t, p, dp, Trigger))
    elif Trigger == 3:
        ro = Density3(t, p)
        return R * 647.096 * JF(t, ro, dt, Trigger)


def Specific_Entropy(t: float, p: float, reg=None) -> float:
    Trigger = Region(t, p) if reg is None else reg

    if Trigger == 1:
        return R * (1386 / (t + 273.15) * JF(t, p, dt, Trigger) - JF(t, p, non, Trigger))
    elif Trigger in [2, 4, 21]:
        return R * (540 / (t + 273.15) * JF(t, p, dt, Trigger) - JF(t, p, non, Trigger))
    elif Trigger == 5:
        return R * (1000 / (t + 273.15) * JF(t, p, dt, Trigger) - JF(t, p, non, Trigger))
    elif Trigger == 3:
        ro = Density3(t, p)
        return R * (647.096 / (t + 273.15) * JF(t, ro, dt, Trigger) - JF(t, ro, non, Trigger))


def Specific_Enthalpy(t: float, p: float, reg=None) -> float:
    Trigger = Region(t, p) if reg is None else reg

    if Trigger == 1:
        return R * 1386 * JF(t, p, dt, Trigger)
    elif Trigger in [2, 4, 21]:
        return R * 540 * JF(t, p, dt, Trigger)
    elif Trigger == 5:
        return R * 1000 * JF(t, p, dt, Trigger)
    elif Trigger == 3:
        ro = Density3(t, p)
        return R * (647.096 * JF(t, ro, dt, Trigger) + (t + 273.15) * JF(t, ro, dp, Trigger) * ro / 322)


def Heat_Capacity_Isobaric(t: float, p: float, reg=None) -> float:
    Trigger = Region(t, p) if reg is None else reg

    if Trigger == 1:
        return -R * (1386 / (t + 273.15)) ** 2 * JF(t, p, dtt, Trigger)
    elif Trigger in [2, 4, 21]:
        return -R * (540 / (t + 273.15)) ** 2 * JF(t, p, dtt, Trigger)
    elif Trigger == 5:
        return -R * (1000 / (t + 273.15)) ** 2 * JF(t, p, dtt, Trigger)
    elif Trigger == 3:
        ro = Density3(t, p)
        tf = 647.096 / (t + 273.15)
        rof = ro / 322
        fp = JF(t, ro, dp, Trigger)
        return (-tf ** 2 * JF(t, ro, dtt, Trigger) + (fp - tf * JF(t, ro, dtp, Trigger)) ** 2 / (
                2 * fp / rof + JF(t, ro, dpp, Trigger))) * R


def Heat_Capacity_Isochoric(t: float, p: float, reg=None) -> float:
    Trigger = Region(t, p) if reg is None else reg

    if Trigger == 1:
        tf = 1386 / (t + 273.15)
        return R * (-tf ** 2 * JF(t, p, dtt, Trigger) + (JF(t, p, dp, Trigger) - tf * JF(t, p, dtp, Trigger)) ** 2 / JF(
            t, p, dpp, Trigger))
    elif Trigger in [2, 4, 21]:
        tf = 540 / (t + 273.15)
        return R * (-tf ** 2 * JF(t, p, dtt, Trigger) + (JF(t, p, dp, Trigger) - tf * JF(t, p, dtp, Trigger)) ** 2 / JF(
            t, p, dpp, Trigger))
    elif Trigger == 5:
        tf = 1000 / (t + 273.15)
        return R * (-tf ** 2 * JF(t, p, dtt, Trigger) + (JF(t, p, dp, Trigger) - tf * JF(t, p, dtp, Trigger)) ** 2 / JF(
            t, p, dpp, Trigger))
    elif Trigger == 3:
        ro = Density3(t, p)
        return -(647.096 / (t + 273.15)) ** 2 * JF(t, ro, dtt, 3) * R


def Speed_Sound(t: float, p: float, reg=None) -> float:
    Trigger = Region(t, p) if reg is None else reg

    if Trigger == 1:
        tf = 1386 / (t + 273.15)
        return sqrt(R * (t + 273.15) * JF(t, p, dp, Trigger) ** 2 / (
                (JF(t, p, dp, Trigger) - tf * JF(t, p, dtp, Trigger)) ** 2 /
                (tf ** 2 * JF(t, p, dtt, Trigger)) - JF(t, p, dpp, Trigger)))
    elif Trigger in [2, 4, 21]:
        tf = 540 / (t + 273.15)
        return sqrt(R * (t + 273.15) * JF(t, p, dp, Trigger) ** 2 / (
                (JF(t, p, dp, Trigger) - tf * JF(t, p, dtp, Trigger)) ** 2 /
                (tf ** 2 * JF(t, p, dtt, Trigger)) - JF(t, p, dpp, Trigger)))
    elif Trigger == 5:
        tf = 1000 / (t + 273.15)
        return sqrt(R * (t + 273.15) * JF(t, p, dp, Trigger) ** 2 / (
                (JF(t, p, dp, Trigger) - tf * JF(t, p, dtp, Trigger)) ** 2 /
                (tf ** 2 * JF(t, p, dtt, Trigger)) - JF(t, p, dpp, Trigger)))
    elif Trigger == 3:
        ro = Density3(t, p)
        tf = 647.096 / (t + 273.15)
        rof = ro / 322
        fp = JF(t, ro, dp, Trigger)
        return (R * (t + 273.15) * rof ** 2 * (
                2 * fp / rof + JF(t, ro, dpp, Trigger) -
                (fp - tf * JF(t, ro, dtp, Trigger)) ** 2 /
                (tf ** 2 * JF(t, ro, dtt, Trigger)))) ** 0.5


def Saturation_Temperature(p: float) -> float:
    N1, n2, N3, n4, n5, n6, n7, n8, n9, n10 = N_Update()
    pf = p ** 0.25
    E = pf ** 2 + N3 * pf + n6
    F = N1 * pf ** 2 + n4 * pf + n7
    G = n2 * pf ** 2 + n5 * pf + n8
    D = 2 * G / (-F - (F ** 2 - 4 * E * G) ** 0.5)
    return (n10 + D - ((n10 + D) ** 2 - 4 * (n9 + n10 * D)) ** 0.5) / 2 - 273.15


def Saturation_Pressure(t: float) -> float:
    N1, n2, N3, n4, n5, n6, n7, n8, n9, n10 = N_Update()
    tf = (t + 273.15) + n9 / (t + 273.15 - n10)
    a = tf ** 2 + N1 * tf + n2
    B = N3 * tf ** 2 + n4 * tf + n5
    C = n6 * tf ** 2 + n7 * tf + n8
    return (2 * C / (-B + (B ** 2 - 4 * a * C) ** 0.5)) ** 4


def Border_Temperature(p: float) -> float:
    if p < 16.5292:
        N1, n2, N3, n4, n5, n6, n7, n8, n9, n10 = N_Update()
        pf = p ** 0.25
        E = pf ** 2 + N3 * pf + n6
        F = N1 * pf ** 2 + n4 * pf + n7
        G = n2 * pf ** 2 + n5 * pf + n8
        D = 2 * G / (-F - (F ** 2 - 4 * E * G) ** 0.5)
        return (n10 + D - ((n10 + D) ** 2 - 4 * (n9 + n10 * D)) ** 0.5) / 2 - 273.15
    else:
        return 572.54459862746 + ((p - 13.91883977887) / 1.0192970039326E-03) ** 0.5 - 273.15


def Border_Pressure(t: float) -> float:
    if t < 350:
        N1, n2, N3, n4, n5, n6, n7, n8, n9, n10 = N_Update()
        tf = (t + 273.15) + n9 / (t + 273.15 - n10)
        a = tf ** 2 + N1 * tf + n2
        B = N3 * tf ** 2 + n4 * tf + n5
        C = n6 * tf ** 2 + n7 * tf + n8
        return (2 * C / (-B + (B ** 2 - 4 * a * C) ** 0.5)) ** 4
    else:
        return 348.05185628969 - 1.1671859879975 * (t + 273.15) + 1.0192970039326E-03 * (t + 273.15) ** 2


def Viscosity(t: float, p: float, reg=None) -> float:
    Trigger = Region(t, p) if reg is None else reg

    tf = (t + 273.15) / 647.096
    rof = Density(t, p, Trigger) / 322
    mu0 = 0
    for i in range(1, 4):
        mu0 = mu0 + VHi[i] / tf ** (i - 1)

    mu0 = 100 * tf ** 0.5 / mu0
    mu1 = 0
    for i in range(1, 21):
        mu1 = mu1 + VHij[i] * (1 / tf - 1) ** Vi[i] * (rof - 1) ** Vj[i]

    mu1 = exp(rof * mu1)
    mu2 = 1
    return mu0 * mu1 * mu2 * 0.000001


def Density_MI(t: float, p: float) -> float:
    tau = (t + 273.15) / 647.14
    Pi = p / 22.064
    return 1000 / (
            114.332 * tau - 431.6382 + 706.5474 / tau - 641.9127 / tau ** 2 + 349.4417 /
            tau ** 3 - 113.8191 / tau ** 4 + 20.5199 / tau ** 5 - 1.578507 / tau ** 6 + Pi *
            (-3.117072 + 6.589303 / tau - 5.210142 / tau ** 2 + 1.819096 / tau ** 3 - 0.2365448 / tau ** 4) +
            Pi ** 2 * (-6.417443 * tau + 19.84842 - 24.00174 / tau + 14.21655
                       / tau ** 2 - 4.13194 / tau ** 3 + 0.4721637 / tau ** 4))


def Specific_Enthalpy_MI(t: float, p: float) -> float:
    tau = (t + 273.15) / 647.14
    Pi = p / 22.064
    return (7809.096 * tau - 13868.72 + 12725.22 / tau - 6370.893 / tau ** 2 + 1595.86 /
            tau ** 3 - 159.9064 / tau ** 4 + Pi * (9.488789 / tau + 1) + Pi ** 2 *
            (-148.1135 * tau + 224.3027 - 111.4602 / tau + 18.15823 / tau ** 2)) * 1000


''' JF and the end '''


def JF(t: float, p: float, Trigger: int, reg: int) -> float:
    jf_ans = 0

    if reg == 1:
        pf = p / 16.53
        tf = 1386 / (t + 273.15)
        jf_ans = 0
        if Trigger == non:
            for i in range(1, 34):
                jf_ans = jf_ans + N1[i] * (7.1 - pf) ** I1[i] * (tf - 1.222) ** J1[i]
        elif Trigger == dt:
            for i in range(1, 34):
                jf_ans = jf_ans + N1[i] * J1[i] * (7.1 - pf) ** I1[i] * (tf - 1.222) ** (J1[i] - 1)
        elif Trigger == dtt:
            for i in range(1, 34):
                jf_ans = jf_ans + N1[i] * J1[i] * (J1[i] - 1) * (7.1 - pf) ** I1[i] * (tf - 1.222) ** (J1[i] - 2)
        elif Trigger == dtp:
            for i in range(1, 34):
                jf_ans = jf_ans - N1[i] * I1[i] * J1[i] * (7.1 - pf) ** (I1[i] - 1) * (tf - 1.222) ** (J1[i] - 1)
        elif Trigger == dp:
            for i in range(1, 34):
                jf_ans = jf_ans - N1[i] * I1[i] * (7.1 - pf) ** (I1[i] - 1) * (tf - 1.222) ** J1[i]
        elif Trigger == dpp:
            for i in range(1, 34):
                jf_ans = jf_ans + N1[i] * I1[i] * (I1[i] - 1) * (7.1 - pf) ** (I1[i] - 2) * (tf - 1.222) ** J1[i]

    elif reg in [2, 4]:
        pf = p
        tf = 540 / (t + 273.15)
        if Trigger == non:
            jf_ans = log(p)
            for i in range(1, 9):
                jf_ans = jf_ans + N02[i] * tf ** J02[i]
            for i in range(1, 43):
                jf_ans = jf_ans + Nr2[i] * pf ** Ir2[i] * (tf - 0.5) ** Jr2[i]
        elif Trigger == dt:
            jf_ans = 0
            for i in range(1, 9):
                jf_ans = jf_ans + N02[i] * J02[i] * tf ** (J02[i] - 1)
            for i in range(1, 43):
                jf_ans = jf_ans + Nr2[i] * pf ** Ir2[i] * Jr2[i] * (tf - 0.5) ** (Jr2[i] - 1)
        elif Trigger == dtt:
            jf_ans = 0
            for i in range(1, 9):
                jf_ans = jf_ans + N02[i] * J02[i] * (J02[i] - 1) * tf ** (J02[i] - 2)
            for i in range(1, 43):
                jf_ans = jf_ans + Nr2[i] * pf ** Ir2[i] * Jr2[i] * (Jr2[i] - 1) * (tf - 0.5) ** (Jr2[i] - 2)
        elif Trigger == dtp:
            jf_ans = 0
            for i in range(1, 43):
                jf_ans = jf_ans + Nr2[i] * Ir2[i] * pf ** (Ir2[i] - 1) * Jr2[i] * (tf - 0.5) ** (Jr2[i] - 1)
        elif Trigger == dp:
            jf_ans = 1 / pf
            for i in range(1, 43):
                jf_ans = jf_ans + Nr2[i] * Ir2[i] * pf ** (Ir2[i] - 1) * (tf - 0.5) ** Jr2[i]
        elif Trigger == dpp:
            jf_ans = -1 / pf ** 2
            for i in range(1, 43):
                jf_ans = jf_ans + Nr2[i] * Ir2[i] * (Ir2[i] - 1) * pf ** (Ir2[i] - 2) * (tf - 0.5) ** Jr2[i]

    elif reg == 21:
        pf = p
        tf = 540 / (t + 273.15)
        if Trigger == non:
            jf_ans = log(p)
            for i in range(1, 9):
                jf_ans = jf_ans + N02m[i] * tf ** J02[i]
            for i in range(1, 13):
                jf_ans = jf_ans + Nr2m[i] * pf ** Ir2m[i] * (tf - 0.5) ** Jr2m[i]
        elif Trigger == dt:
            jf_ans = 0
            for i in range(1, 9):
                jf_ans = jf_ans + N02m[i] * J02[i] * tf ** (J02[i] - 1)
            for i in range(1, 13):
                jf_ans = jf_ans + Nr2m[i] * pf ** Ir2m[i] * Jr2m[i] * (tf - 0.5) ** (Jr2m[i] - 1)
        elif Trigger == dtt:
            jf_ans = 0
            for i in range(1, 9):
                jf_ans = jf_ans + N02m[i] * J02[i] * (J02[i] - 1) * tf ** (J02[i] - 2)
            for i in range(1, 13):
                jf_ans = jf_ans + Nr2m[i] * pf ** Ir2m[i] * Jr2m[i] * (Jr2m[i] - 1) * (tf - 0.5) ** (Jr2m[i] - 2)
        elif Trigger == dtp:
            jf_ans = 0
            for i in range(1, 13):
                jf_ans = jf_ans + Nr2m[i] * Ir2m[i] * pf ** (Ir2m[i] - 1) * Jr2m[i] * (tf - 0.5) ** (Jr2m[i] - 1)
        elif Trigger == dp:
            jf_ans = 1 / pf
            for i in range(1, 13):
                jf_ans = jf_ans + Nr2m[i] * Ir2m[i] * pf ** (Ir2m[i] - 1) * (tf - 0.5) ** Jr2m[i]
        elif Trigger == dpp:
            jf_ans = -1 / pf ** 2
            for i in range(1, 13):
                jf_ans = jf_ans + Nr2m[i] * Ir2m[i] * (Ir2m[i] - 1) * pf ** (Ir2m[i] - 2) * (tf - 0.5) ** Jr2m[i]

    elif reg == 3:
        rof = p / 322
        tf = 647.096 / (t + 273.15)
        if Trigger == non:
            jf_ans = 1.0658070028513 * log(rof)
            for i in range(1, 39):
                jf_ans = jf_ans + N3[i] * rof ** I3[i] * tf ** J3[i]
        elif Trigger == dt:
            jf_ans = 0
            for i in range(1, 39):
                jf_ans = jf_ans + N3[i] * rof ** I3[i] * J3[i] * tf ** (J3[i] - 1)
        elif Trigger == dtt:
            jf_ans = 0
            for i in range(1, 39):
                jf_ans = jf_ans + N3[i] * rof ** I3[i] * J3[i] * (J3[i] - 1) * tf ** (J3[i] - 2)
        elif Trigger == dtp:
            jf_ans = 0
            for i in range(1, 39):
                jf_ans = jf_ans + N3[i] * I3[i] * rof ** (I3[i] - 1) * J3[i] * tf ** (J3[i] - 1)
        elif Trigger == dp:
            jf_ans = 1.0658070028513 / rof
            for i in range(1, 39):
                jf_ans = jf_ans + N3[i] * I3[i] * rof ** (I3[i] - 1) * tf ** J3[i]
        elif Trigger == dpp:
            jf_ans = -1.0658070028513 / rof ** 2
            for i in range(1, 39):
                jf_ans = jf_ans + N3[i] * I3[i] * (I3[i] - 1) * rof ** (I3[i] - 2) * tf ** J3[i]

    elif reg == 5:
        pf = p
        tf = 1000 / (t + 273.15)
        if Trigger == non:
            jf_ans = log(p)
            for i in range(1, 6):
                jf_ans = jf_ans + N05[i] * tf ** J05[i]
            for i in range(1, 6):
                jf_ans = jf_ans + Nr5[i] * pf ** Ir5[i] * tf ** Jr5[i]
        elif Trigger == dt:
            jf_ans = 0
            for i in range(1, 6):
                jf_ans = jf_ans + N05[i] * J05[i] * tf ** (J05[i] - 1)
            for i in range(1, 6):
                jf_ans = jf_ans + Nr5[i] * pf ** Ir5[i] * Jr5[i] * tf ** (Jr5[i] - 1)
        elif Trigger == dtt:
            jf_ans = 0
            for i in range(1, 6):
                jf_ans = jf_ans + N05[i] * J05[i] * (J05[i] - 1) * tf ** (J05[i] - 2)
            for i in range(1, 6):
                jf_ans = jf_ans + Nr5[i] * pf ** Ir5[i] * Jr5[i] * (Jr5[i] - 1) * tf ** (Jr5[i] - 2)
        elif Trigger == dtp:
            jf_ans = 0
            for i in range(1, 6):
                jf_ans = jf_ans + Nr5[i] * Ir5[i] * pf ** (Ir5[i] - 1) * Jr5[i] * tf ** (Jr5[i] - 1)
        elif Trigger == dp:
            jf_ans = 1 / pf
            for i in range(1, 6):
                jf_ans = jf_ans + Nr5[i] * Ir5[i] * pf ** (Ir5[i] - 1) * tf ** Jr5[i]
        elif Trigger == dpp:
            jf_ans = -1 / pf ** 2
            for i in range(1, 6):
                jf_ans = jf_ans + Nr5[i] * Ir5[i] * (Ir5[i] - 1) * pf ** (Ir5[i] - 2) * tf ** Jr5[i]

    return jf_ans
