import json
import matplotlib.pyplot as plt

filename = 'trades_backup.json'

with open(filename, 'r') as file:
    data = json.load(file)

# Функция для фильтрации данных по 3-му элементу ключа
def filter_data(data, filter_value):
    return {key: values for key, values in data.items() if eval(key)[2] == filter_value}

# Функция обработки данных
def process_data(data):
    keys, sums, counts = [], [], []
    total_count = 0
    
    for key, values in data.items():
        total_sum = sum(values)
        count = len(values)
        total_count += count
        keys.append(key)
        sums.append(total_sum)
        counts.append(count)

    # Сортируем данные по средним значениям (sums / counts)
    sorted_data = sorted(zip(keys, sums, counts), key=lambda x: x[1] / x[2] if x[2] > 0 else 0)
    sorted_keys, sorted_sums, sorted_counts = zip(*sorted_data) if sorted_data else ([], [], [])
    sorted_avgs = [s / c if c > 0 else 0 for s, c in zip(sorted_sums, sorted_counts)]
    
    total_sum_all = sum(sums)
    average_value = total_sum_all / total_count if total_count > 0 else 0
    
    return sorted_keys, sorted_sums, sorted_counts, sorted_avgs, total_sum_all, total_count, average_value

# Фильтруем данные
data_0 = filter_data(data, 0)
data_10 = filter_data(data, 10)
data_5 = filter_data(data, 5)

# Обрабатываем
sorted_keys_0, sorted_sums_0, sorted_counts_0, sorted_avgs_0, total_sum_0, total_count_0, avg_0 = process_data(data_0)
sorted_keys_10, sorted_sums_10, sorted_counts_10, sorted_avgs_10, total_sum_10, total_count_10, avg_10 = process_data(data_10)
sorted_keys_5, sorted_sums_5, sorted_counts_5, sorted_avgs_5, total_sum_5, total_count_5, avg_5 = process_data(data_5)

# Создаем 3 строки графиков (по 3 в каждой)
fig, axes = plt.subplots(3, 3, figsize=(36, 30))  # Увеличена высота графиков
fig.subplots_adjust(wspace=1.2, hspace=0.5)

titles = [
    "Number of terms (0)", "Sorting by sum (0)", "Average per entry (0)",
    "Number of terms (5)", "Sorting by sum (5)", "Average per entry (5)",
    "Number of terms (10)", "Sorting by sum (10)", "Average per entry (10)"
]

# Данные для графиков, отсортированные по средним значениям (sorted_avgs)
datasets = [
    (sorted_keys_0, sorted_counts_0, 'lightblue'),
    (sorted_keys_0, sorted_sums_0, 'lightcoral'),
    (sorted_keys_0, sorted_avgs_0, 'lightgreen'),
    (sorted_keys_5, sorted_counts_5, 'lightblue'),
    (sorted_keys_5, sorted_sums_5, 'lightcoral'),
    (sorted_keys_5, sorted_avgs_5, 'lightgreen'),
    (sorted_keys_10, sorted_counts_10, 'lightblue'),
    (sorted_keys_10, sorted_sums_10, 'lightcoral'),
    (sorted_keys_10, sorted_avgs_10, 'lightgreen')
]

for i, ax in enumerate(axes.flat):
    keys, values, color = datasets[i]
    bars = ax.barh(keys, values, color=color)
    ax.set_xlabel(titles[i], fontsize=5)
    ax.set_ylabel("Headers", fontsize=5)
    ax.set_title(titles[i], fontweight='bold', fontsize=5)

    # Уменьшаем размер текста на шкалах
    ax.tick_params(axis='both', which='major', labelsize=5)

    # Убираем границы графиков
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Добавляем подписи
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2, f'{width:.2f}', 
                va='center', fontsize=7, fontweight='bold')

print(f'TOTAL SUM (0): {total_sum_0}')
print(f'TOTAL CNT (0): {total_count_0}')
print(f'TOTAL AVG (0): {avg_0}')

print(f'TOTAL SUM (5): {total_sum_5}')
print(f'TOTAL CNT (5): {total_count_5}')
print(f'TOTAL AVG (5): {avg_5}')

print(f'TOTAL SUM (10): {total_sum_10}')
print(f'TOTAL CNT (10): {total_count_10}')
print(f'TOTAL AVG (10): {avg_10}')

plt.show()
