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
        result.append([[], border, mid, 0.0, 0.0])
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

def main(data):
    sorted_data = data; sorted_data.sort()

    mean = statistics.mean(data)
    print(f'1. Мат.ожидание = {mean}')

    offset_variance = f2_3(data, mean)
    print(f'2/3. Смещенная оценка дисперсии = {offset_variance}')

    non_offset_variance = f4(offset_variance, len(data))
    print(f'4. Не смещенная оценка дисперсии = {non_offset_variance}')

    median = f5(sorted_data)
    print(f'5. Медиана = {median}')

    width_of_distribution = f_R(sorted_data)
    print(f'R. Размах варьирования = {width_of_distribution}')

    l = 12 # Кол-во интервалов
    interval_width = f6_7(width_of_distribution, l)
    print(f'6. Ширина интервала = {interval_width}')

    intervals = make_intervals(sorted_data, l, interval_width)
    print('Таблица 3:')
    print_intervals(intervals)

    show_plots(intervals, interval_width)

if __name__ == "__main__":
    main(data_collection.example)
