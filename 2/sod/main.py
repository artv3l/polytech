import statistics
import math
import matplotlib.pyplot as plt
import scipy

import data as data_collection

def f2_3(data, mean):
    result = 0
    for i in data:
        result += (i - mean)**2
    return result / len(data)

def f4(offset_variance, n):
    return n * offset_variance / (n-1)

def f5(sorted_data):
    result = 0
    n = len(sorted_data)
    if n % 2 == 0:
        k = n // 2
        result = (sorted_data[k-1] + sorted_data[k]) / 2
    else:
        k = (n - 1) // 2
        result = sorted_data[k]
    return result

def f_R(sorted_data):
    return math.ceil(max(sorted_data) - min(sorted_data))

def f6_7(width_of_distribution, l):
    return width_of_distribution / l

def make_intervals(sorted_data, l, interval_width):
    result = []

    begin = min(sorted_data)
    for i in range(l):
        border = [begin, begin + interval_width]
        mid = begin + (border[1] - border[0]) / 2
        result.append([[], border, mid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        begin += interval_width

    for val in sorted_data:
        for i_res in range(len(result)):
            if i_res == 0 and val < result[i_res][1][1]:
                result[i_res][0].append(val)
            elif (i_res == len(result) - 1) and val > result[i_res][1][0]:
                result[i_res][0].append(val)
            elif result[i_res][1][0] < val <= result[i_res][1][1]:
                result[i_res][0].append(val)

    for res in result:
        res[3] = len(res[0])
        res[4] = res[3] / 100

    return result

def print_intervals(intervals):
    num = 1
    for interval in intervals:
        print(f'{num:3} | {interval[1][0]:8.2f} : {interval[1][1]:8.2f} | {interval[3]:4} | {interval[4]:6} | {interval[2]:8.2f}')
        num += 1

def show_plots(intervals, interval_width):
    x = [i[2] for i in intervals]
    y = [i[4] for i in intervals]
    xticks = [i[1][0] for i in intervals]; xticks.append(intervals[-1][1][1])
    
    plt.plot(x, y)
    plt.xticks(xticks)
    plt.grid()
    plt.xlabel('Интервал'); plt.ylabel('Частотность'); plt.title('Полигон')
    plt.show()

    plt.bar(x, y, width=interval_width)
    plt.xticks(xticks)
    plt.grid()
    plt.xlabel('Интервал'); plt.ylabel('Частотность'); plt.title('Гистограмма')
    plt.show()

    accum_freq = [sum(y[:i+1]) for i in range(len(y))]
    accum_freq.insert(0, 0); accum_freq.append(1)
    x_for_freq = x.copy(); x_for_freq.insert(0, intervals[0][1][0]); x_for_freq.append(intervals[-1][1][1])

    plt.step(x_for_freq, accum_freq, where='post')
    plt.xticks(xticks)
    plt.grid()
    plt.xlabel('Интервал'); plt.ylabel('Накопленная частотность'); plt.title('Ступенчатая кривая')
    plt.show()

def f8(intervals, n):
    xv = [(i[2] * i[3]) for i in intervals]
    return sum(xv) / n

def f9(intervals, mean_intervals, n):
    x2v = [(i[2]**2 * i[3]) for i in intervals]
    s2 = (sum(x2v) / n) - mean_intervals**2
    return s2

def calc_mode(intervals):
    interval = max(intervals, key=lambda i: i[3])
    return interval[2]

def calc_sheppard(s2, interval_width, l):
    return s2 - (interval_width**2 / l)

def f11(intervals, false_zero, interval_width):
    for i in intervals:
        i[5] = (i[2] - false_zero) / interval_width

def print_intervals_4(intervals):
    num = 1
    for interval in intervals:
        print(f'{num:3} | {interval[2]:6.2f} | {interval[5]:6.2f}')
        num += 1

def calc_m(intervals, n, interval_width, false_zero):
    def calc_h(intervals, num, n):
        vy = [(i[3] * i[5]**num) for i in intervals]
        return sum(vy) / n

    [h1, h2, h3, h4] = [calc_h(intervals, i, n) for i in range(1, 5)]
    m1 = interval_width * h1 + false_zero
    m2 = interval_width**2 * (h2 - h1**2)
    m3 = interval_width**3 * (h3 - (3 * h1 * h2) + (2 * h1**3))
    m4 = interval_width**4 * (h4 - (4 * h1 * h3) + (6 * h1**2 * h2) - (3 * h1**4))

    return [m1, m2, m3, m4]

def f17_for_5_19(mean_cfi, offset_variance_cfi, n):
    t_5_19 = 2.093
    temp = t_5_19 * (offset_variance_cfi / math.sqrt(n-1))
    cfi_min = mean_cfi - temp
    cfi_max = mean_cfi + temp
    return cfi_min, cfi_max

def calc_cfi_for_variance(n, offset_variance_cfi):
    hi1 = 8.567; hi2 = 33.7
    cfi_min = n * offset_variance_cfi**2 / hi2
    cfi_max = n * offset_variance_cfi**2 / hi1
    return cfi_min, cfi_max

def f18(n):
    return math.sqrt((6 * (n - 1)) / ((n + 1) * (n + 3)))

def f19(n):
    a = 24 * n * (n - 2) * (n - 3)
    b = (n - 1)**2 * (n + 3) * (n + 5)
    return math.sqrt(a / b)

def calc_table7(intervals, variance, mean, n):
    npi_min = 5
    s = variance**0.5

    npi_temp = 0.0
    v_temp = 0

    def cdf(x):
        return scipy.stats.norm.cdf(x) - 0.5

    for i in range(len(intervals)):
        interval = intervals[i]

        borders = interval[1]
        if i == 0:
            borders[0] = -math.inf
        elif i == len(intervals) - 1:
            borders[1] = math.inf

        sigma = (borders[1] - mean) / s

        a = cdf((borders[1] - mean) / s)
        b = cdf((borders[0] - mean) / s)
        pi = a - b

        npi = npi_temp + n * pi
        v = v_temp + interval[3]
        if npi < npi_min and i != len(intervals) - 1:
            npi_temp = npi
            v_temp = v
            npi = 0.0
            v = 0
        else:
            npi_temp = 0.0
            v_temp = 0

        interval[6] = sigma
        interval[7] = a
        interval[8] = pi
        interval[9] = npi
        interval[10] = v

    i = -2
    while intervals[-1][9] < npi_min:
        for j in range(9, 11):
            intervals[-1][j] += intervals[i][j]
            intervals[i][j] = 0.0
        i -= 1

    for interval in intervals:
        interval[11] = interval[10] - interval[9]
        interval[12] = interval[11]**2 / interval[9] if interval[10] != 0 else 0

def print_table7(intervals):
    num = 1
    kv_sum = 0.0
    for interval in intervals:
        print(f'  {num:2} | {interval[1][0]:8.2f} : {interval[1][1]:8.2f} | {interval[6]:8.4f} | {interval[7]:8.4f} | {interval[8]:8.4f} | {interval[9]:8.4f} | {interval[10]:4} | {interval[11]:8.4f} | {interval[12]:8.4f}')
        num += 1
        kv_sum += interval[12]
    print(f'  sum = {kv_sum}')

def main(data, is_show_plots):
    sorted_data = data.copy(); sorted_data.sort()
    n = len(data)

    mean = statistics.mean(data)
    print(f'1. Мат.ожидание = {mean}')

    offset_variance = f2_3(data, mean)
    print(f'2/3. Смещенная оценка дисперсии = {offset_variance}')

    non_offset_variance = f4(offset_variance, n)
    print(f'4. Несмещенная оценка дисперсии = {non_offset_variance}')

    median = f5(sorted_data)
    print(f'5. Медиана = {median}')

    width_of_distribution = f_R(sorted_data)
    print(f'R. Размах варьирования = {width_of_distribution}')

    l = 12 # Кол-во интервалов
    interval_width = f6_7(width_of_distribution, l)
    print(f'6. Ширина интервала = {interval_width}')

    # [ 0 - Элементы из исходной выборки, 1 - Границы[min, max],
    # 2 - Середина интервала, 3 - Частота, 4 - Частотность,
    # 5 - Отностительные серединаы интервалов, 6 - В доялх сигма ]
    intervals = make_intervals(sorted_data, l, interval_width)
    print('Таблица 3:')
    print_intervals(intervals)

    if is_show_plots:
        show_plots(intervals, interval_width)

    mean_intervals = f8(intervals, n)
    print(f'8. Среднее арифметическое по интервалам = {mean_intervals}')

    s2 = f9(intervals, mean_intervals, n)
    print(f'9. Эмпирическая оценка дисперсии s^2 = {s2}')

    s = s2**0.5 # f10
    print(f'10. Эмпирическая оценка дисперсии s = {s}')

    v = s / mean_intervals
    print(f'Коэффициент вариации v = {v}')

    mode = calc_mode(intervals)
    print(f'Мода = {mode}')

    s_sheppard = calc_sheppard(s2, interval_width, l)
    print(f'Несмещенная оценка дисперсии (с поправкой Шеппарда) = {s_sheppard}')

    false_zero = mode
    f11(intervals, false_zero, interval_width)
    print_intervals_4(intervals)

    m_list = calc_m(intervals, n, interval_width, false_zero)
    for i in range(len(m_list)):
        print(f'm{i+1} = {m_list[i]}')
    
    asymmetry = m_list[3-1] / s**3
    print(f'Асимметрия = {asymmetry}')

    excess = (m_list[4-1] / s**4) - 3
    print(f'Эксцесс = {excess}')

    print('Доверительные интервалы')
    n_cfi = 20 # cfi - Confidence interval
    data_cfi = data[:n_cfi]
    
    mean_cfi = statistics.mean(data_cfi)
    print(f'  Мат.ожидание (для 20 элементов) = {mean_cfi}')
    
    offset_variance_cfi_2 = f2_3(data_cfi, mean_cfi)
    offset_variance_cfi = offset_variance_cfi_2**0.5
    print(f'  Смещенная оценка дисперсии = {offset_variance_cfi_2}')

    non_offset_variance_cfi = f4(offset_variance_cfi_2, n_cfi)
    print(f'  Несмещенная оценка дисперсии s^2 = {non_offset_variance_cfi}')
    
    non_offset_variance_cfi_sqrt = non_offset_variance_cfi**0.5
    print(f'  Несмещенная оценка дисперсии s = {non_offset_variance_cfi_sqrt}')

    q = 5
    t_5_19 = 2.093
    print(f'  n-1 = {n_cfi-1} ; q = {q} ; t_5_19 = {t_5_19}')

    print('  Для математического ожидания')
    cfi_min, cfi_max = f17_for_5_19(mean_cfi, offset_variance_cfi, n_cfi)
    print(f'    cfi_min = {cfi_min} ; cfi_max = {cfi_max}')
    
    print('  Для дисперсии')
    cfi_min, cfi_max = calc_cfi_for_variance(n_cfi, offset_variance_cfi)
    print(f'    cfi_min^2 = {cfi_min} ; cfi_max^2 = {cfi_max}')
    print(f'    cfi_min = {cfi_min**0.5} ; cfi_max = {cfi_max**0.5}')

    sigma_sk = f18(n)
    sigma_ek = f19(n)
    print(f'sigma_sk = {sigma_sk} ; sigma_ek = {sigma_ek}')

    print('Критерий Хи-квадрат')
    calc_table7(intervals, s2, mean_intervals, n)
    print(f'  {s2**0.5}, {mean_intervals}, {n}')
    print_table7(intervals)

    print('Критерий знаков')
    znaks = []
    for i in range(21):
        znaks.append(data[i] - data[n - 20 - 1 + i])
    plus_count = len([x for x in znaks if x > 0])
    print(f'  + {plus_count} | - {20 - plus_count}')

    print('Критерий Вилкоксона')
    d = [[i, 'x'] for i in data[:20]] + [[i, 'y'] for i in data[n-20:]]
    d.sort(key=lambda x: x[0])
    u = 0
    for i in range(len(d)):
        if d[i][1] == 'x':
            u += len([x for x in d[:i] if x[1] == 'y'])
    print(f'  u = {u}')
    
if __name__ == "__main__":
    main(data_collection.var3, is_show_plots=False)
