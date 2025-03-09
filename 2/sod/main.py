import statistics
import math
import matplotlib.pyplot as plt

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
        border = (begin, begin + interval_width)
        mid = begin + (border[1] - border[0]) / 2
        result.append([[], border, mid, 0.0, 0.0, 0.0])
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

def main(data):
    sorted_data = data; sorted_data.sort()
    n = len(data)

    mean = statistics.mean(data)
    print(f'1. Мат.ожидание = {mean}')

    offset_variance = f2_3(data, mean)
    print(f'2/3. Смещенная оценка дисперсии = {offset_variance}')

    non_offset_variance = f4(offset_variance, n)
    print(f'4. Не смещенная оценка дисперсии = {non_offset_variance}')

    median = f5(sorted_data)
    print(f'5. Медиана = {median}')

    width_of_distribution = f_R(sorted_data)
    print(f'R. Размах варьирования = {width_of_distribution}')

    l = 12 # Кол-во интервалов
    interval_width = f6_7(width_of_distribution, l)
    print(f'6. Ширина интервала = {interval_width}')

    # [0 - Элементы из исходной выборки, 1 - Границы[min, max], 2 - Середина интервала, 3 - Частота, 4 - Частотность, 5 - Отностительные серединаы интервалов]
    intervals = make_intervals(sorted_data, l, interval_width)
    print('Таблица 3:')
    print_intervals(intervals)

    #show_plots(intervals, interval_width)

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



if __name__ == "__main__":
    main(data_collection.example)
