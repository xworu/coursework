from datetime import timedelta
from coursework.common import check_amount, get_time_slots, print_schedule
import random
import matplotlib.pyplot as plt

# Функция для создания случайного расписания с соблюдением базовых требований
def generate_random_schedule(condition_met, route_duration):
    schedule = {day: {} for day in range(7)}
    driver_shifts = {}
    drivers_type1 = []
    drivers_type2 = []
    total_work_time = {}  # Отслеживает общее рабочее время водителей

    max_work_time = {"T1": timedelta(hours=9), "T2": timedelta(hours=13)}

    for driver in drivers_type1 + drivers_type2:
      driver_shifts[driver] = []

    for day in range(7):
        slots = get_time_slots(day, condition_met)
        day_schedule = {}
        had_lunch = {}  # Отслеживает обеды для водителей первого типа
        route_count = {}  # Счётчик маршрутов для второго типа

        for slot in slots:
            driver_type = random.choice(["T1", "T2"])
            assigned_driver = None
            available_drivers = drivers_type1 if driver_type == 'T1' else drivers_type2
            random.shuffle(available_drivers)

            # Ищем доступного водителя
            for driver in available_drivers:
                if driver not in total_work_time:
                    total_work_time[driver] = timedelta()
                if driver_type == "T1" and driver not in had_lunch:
                    had_lunch[driver] = False
                if driver_type == "T2" and driver not in route_count:
                    route_count[driver] = 0

                if total_work_time[driver] + route_duration > max_work_time[driver_type]:
                    continue
                if driver_type == 'T1' and (day > 4 or slot.hour >= 23 or slot.hour < 8):
                  continue
                assigned_driver = driver
                break

            # Если водителя нет, создаём нового
            if assigned_driver is None:
                if driver_type == "T1":
                    assigned_driver = f"T1_{len(drivers_type1) + 1}"
                    drivers_type1.append(assigned_driver)
                    had_lunch[assigned_driver] = False
                else:
                    assigned_driver = f"T2_{len(drivers_type2) + 1}"
                    drivers_type2.append(assigned_driver)
                    route_count[assigned_driver] = 0
                driver_shifts[assigned_driver] = []
                total_work_time[assigned_driver] = timedelta()

            # Назначаем маршрут
            day_schedule[slot] = (assigned_driver, "Маршрут")
            driver_shifts[assigned_driver].append((day, slot, slot + route_duration, "Маршрут"))
            total_work_time[assigned_driver] += route_duration

            # Учитываем обед для водителей первого т ипа
            if driver_type == "T1" and 13 <= slot.hour < 15 and not had_lunch[assigned_driver]:
              # Водитель уходит на обед, назначаем другого водителя на маршрут в это время
              substitute_driver = None
              for other_driver in drivers_type1:
                if other_driver != assigned_driver and total_work_time[other_driver] + route_duration <= max_work_time['T1']:
                  substitute_driver = other_driver
                  break

              if substitute_driver:
                day_schedule[slot] = (substitute_driver, "Маршрут")
                driver_shifts[substitute_driver].append((day, slot, slot + route_duration, "Маршрут"))
                total_work_time[substitute_driver] += route_duration
              else:
                new_driver = f"T1_{len(drivers_type1) + 1}"
                drivers_type1.append(new_driver)
                driver_shifts[new_driver] = []
                total_work_time[new_driver] = timedelta()
                had_lunch[new_driver] = False

                day_schedule[slot] = (new_driver, "Маршрут")
                driver_shifts[new_driver].append((day, slot, slot + route_duration, "Маршрут"))
                total_work_time[new_driver] += route_duration

              day_schedule[slot] = (substitute_driver, f" Водитель {assigned_driver}: oбед")
              driver_shifts[assigned_driver].append((day, slot, slot + timedelta(hours=1), "Обед"))
              total_work_time[assigned_driver] += timedelta(hours=1)
              had_lunch[assigned_driver] = True

            # Учитываем перерывы для водителей второго типа
            if driver_type == "T2":
              route_count[assigned_driver] += 1
              if route_count[assigned_driver] == 2:
                break_time = timedelta(minutes=20)
                # Водитель уходит на перерыв, назначаем другого водителя на маршрут
                substitute_driver = None
                for other_driver in drivers_type2:
                  if other_driver != assigned_driver and total_work_time[other_driver] + route_duration <= max_work_time['T2']:
                    substitute_driver = other_driver
                    break

                if substitute_driver:
                  day_schedule[slot] = (substitute_driver, "Маршрут")
                  driver_shifts[substitute_driver].append((day, slot, slot + route_duration, "Маршрут"))
                  total_work_time[substitute_driver] += route_duration
                else:
                  new_driver = f"T2_{len(drivers_type2) + 1}"
                  drivers_type2.append(new_driver)
                  driver_shifts[new_driver] = []
                  total_work_time[new_driver] = timedelta()
                  route_count[new_driver] = 0

                  day_schedule[slot] = (new_driver, "Маршрут")
                  driver_shifts[new_driver].append((day, slot, slot + route_duration, "Маршрут"))
                  total_work_time[new_driver] += route_duration

                day_schedule[slot] = (assigned_driver, "Перерыв")
                driver_shifts[assigned_driver].append((day, slot, slot + break_time, "Перерыв"))
                total_work_time[assigned_driver] += break_time
                route_count[assigned_driver] = 0

        schedule[day] = day_schedule

    return schedule, driver_shifts, drivers_type1, drivers_type2


# Оценка качества расписания
def fitness(schedule, driver_shifts):
    penalty = 0

    for driver, shifts in driver_shifts.items():
        total_work_time = timedelta()
        had_lunch = False
        valid_shift = True
        for day, start, end, activity in shifts:
            if activity == "Маршрут":
                total_work_time += end - start
            if activity == "Обед":
                had_lunch = True
            if "T1" in driver:
              if day > 4:
                valid_shift = False
            if "T2" in driver:
              day_of_cycle = day % 4
              if day_of_cycle >= 2:
                valid_shift = False

        if not valid_shift:
          penalty += 10
        if "T1" in driver:
            if total_work_time > timedelta(hours=9):
                penalty += 5
            if not had_lunch:
                penalty += 10
        if "T2" in driver and total_work_time > timedelta(hours=13):
            penalty += 5

    return 100 / (1 + penalty)


# Селекция
def select_population(population, fitness_scores):
  sorted_population = [population[i] for i in sorted(range(len(fitness_scores)), key=lambda x: fitness_scores[x], reverse=True)]
  elite_count = max(1, int(len(sorted_population) * 0.5))
  return sorted_population[:elite_count]


# Кроссинговер
def crossingover(parent1, parent2):
    child_schedule = {}
    child_shifts = {}
    child_drivers_type1 = list(set(parent1[2]) | set(parent2[2]))
    child_drivers_type2 = list(set(parent1[3]) | set(parent2[3]))

    for day in range(7):
        # Берем часть расписания от первого родителя, часть от второго
        if random.random() > 0.5:
            child_schedule[day] = parent1[0][day]
        else:
            child_schedule[day] = parent2[0][day]

    # Объединяем смены водителей, избегая дублирования
    for driver, shifts in {**parent1[1], **parent2[1]}.items():
        if driver not in child_shifts:
            child_shifts[driver] = shifts

    return child_schedule, child_shifts, child_drivers_type1, child_drivers_type2

# Мутация
def mutate(schedule, drivers_type1, drivers_type2, driver_shifts):
    for day in schedule:
        if random.random() < 0.5:
            if not schedule[day]:
                continue

            # Случайное время и водитель
            random_time = random.choice(list(schedule[day].keys()))
            current_driver, activity = schedule[day][random_time]

            if random.random() < 0.5:  # Изменяем водителя
                if "T1" in current_driver and drivers_type1:
                    new_driver = random.choice(drivers_type1)
                elif "T2" in current_driver and drivers_type2:
                    new_driver = random.choice(drivers_type2)
                else:
                    continue
                schedule[day][random_time] = (new_driver, activity)
            if activity == "Перерыв" and random.random() < 0.5: #С вероятностью 50% увеличиваем перерыв на 10-20 минут
                new_end_time = random_time + timedelta(minutes=random.randint(10, 20))
                schedule[day][new_end_time] = schedule[day].pop(random_time)

    return schedule

# Добавление новых индивидов в популяцию
def inject_random_individuals(population, condition_met, route_duration, num=5):
  for _ in range(num):
    random_schedule = generate_random_schedule(condition_met, route_duration)
  population.append(random_schedule)
  return population

# Удаление дубликатов
def remove_duplicates(population):
  unique_population = []
  seen_schedules = set()

  for individual in population:
    schedule_str = str(individual)
    if schedule_str not in seen_schedules:
      seen_schedules.add(schedule_str)
      unique_population.append(individual)
  return unique_population

def update_elite_archive(population, fitness_scores, elite_archive, archive_size=5):
  # Сортируем текущую популяцию
  sorted_population = [population[i] for i in sorted(range(len(fitness_scores)), key=lambda x: fitness_scores[x], reverse=True)]
  combined_elite = elite_archive + sorted_population[:archive_size]
  combined_elite = list({str(ind): ind for ind in combined_elite}.values())
  combined_elite = sorted(combined_elite, key=lambda ind: fitness(ind[0], ind[1]), reverse=True)
  return combined_elite[:archive_size]

# Генетический алгоритм
def genetic_algorithm(generations=100, population_size=30):
    route_duration = timedelta(hours=1, minutes=30)
    num_busses = 30
    condition_met = check_amount(int(route_duration.total_seconds() / 60), num_busses)
    if condition_met < 0:
        return
    population = [generate_random_schedule(condition_met, route_duration) for _ in range(population_size)]
    fitness_history = []
    elite_archive = []


    for generation in range(generations):
        fitness_scores = [fitness(ind[0], ind[1]) for ind in population]
        fitness_history.append(max(fitness_scores))

        # Вывод приспособленности каждого индивидуума
        print(f"Поколение {generation}:")
        for i, score in enumerate(fitness_scores):
            print(f"  Индивидуум {i}: Приспособленность {score}")

        print(f"  Лучшая приспособленность: {max(fitness_scores)}")

        elite_archive = update_elite_archive(population, fitness_scores, elite_archive)
        #Селекция
        selected_population = select_population(population, fitness_scores)
        #Скрещмвание
        next_generation = []

        while len(next_generation) < population_size:
            parent1, parent2 = random.sample(selected_population, 2)
            child = crossingover(parent1, parent2)
            next_generation.append(child)

        population = [
            (mutate(ind[0], ind[2], ind[3], ind[1]), ind[1], ind[2], ind[3])
            for ind in next_generation
        ]
        population += elite_archive
        population = inject_random_individuals(population, condition_met, route_duration)

        population = remove_duplicates(population)

    # Построение графика изменения приспособленности
    plt.plot(fitness_history)
    plt.xlabel("Поколение")
    plt.ylabel("Приспособленность")
    plt.title("Эволюция приспособленности")
    plt.show()

    best_schedule, driver_shifts, drivers_type1, drivers_type2 = max(
        population, key=lambda x: fitness(x[0], x[1])
    )
    return best_schedule, driver_shifts, drivers_type1, drivers_type2


# Запуск алгоритма
best_schedule, driver_shifts, drivers_type1, drivers_type2 = genetic_algorithm()
print_schedule(best_schedule, drivers_type1, drivers_type2, driver_shifts)