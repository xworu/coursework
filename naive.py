from datetime import timedelta
from coursework.common import check_amount, get_time_slots, print_schedule

def is_driver_available(driver_end_time, slot):
    """
    Проверяет, доступен ли водитель для нового маршрута
    """
    return driver_end_time is None or slot >= driver_end_time


def generate_work_days(start_day):
  """
  Генерирует список рабочих дней для водителей второго типа (2/2)
  """
  work_days = []
  for i in range(7):
    if (i - start_day) % 4 in (0, 1):
      work_days.append(i)
  return work_days

def assign_driver(drivers, slot, last_route_end_time,
                  driver_type, driver_shifts, total_work_time,
                  max_work_time, route_duration, had_lunch=None,
                  driver_work_days=None, day=None):
    """
    Возвращает доступного водителя, либо добавляет нового
    """
    # Если список водителей пуст, создаем первого
    if not drivers:
        new_driver = f"{driver_type}_{len(drivers) + 1}"
        drivers.append(new_driver)

        if driver_type == "T1" and had_lunch is not None and new_driver not in had_lunch:
          had_lunch[new_driver] = False

        if driver_type == "T2" and driver_work_days is not None:
          driver_work_days[new_driver] = generate_work_days(day)

        driver_shifts[new_driver] = []
        total_work_time[new_driver] = timedelta()
        return new_driver

    # Проверяем доступных водителей
    for driver in drivers:
      start_time = driver_shifts[driver][0][1] if driver_shifts[driver] else slot
      total_driver_work_time = total_work_time.get(driver, timedelta())

      if driver_type == "T2" and driver_work_days is not None:
        if day not in driver_work_days.get(driver, []):
          continue

      if (is_driver_available(last_route_end_time.get(driver), slot)
      and total_driver_work_time + route_duration <= max_work_time
          and slot + route_duration <= start_time + max_work_time):
            return driver

    # Если никто не доступен, создаем нового
    new_driver = f"{driver_type}_{len(drivers) + 1}"
    drivers.append(new_driver)

    if driver_type == "T1" and had_lunch is not None:
      had_lunch[new_driver] = False

    if driver_type == "T2" and driver_work_days is not None:
      driver_work_days[new_driver] = generate_work_days(day)

    driver_shifts[new_driver] = []
    total_work_time[new_driver] = timedelta()
    return new_driver


def generate_schedule(route_duration=timedelta(hours=1, minutes=30),
                      max_shift_hours_type1=9,
                      max_shift_hours_type2=13):
    """
    Генерирует расписание.
    """
    num_busses = 15
    condition_met = check_amount(int(route_duration.total_seconds() / 60), num_busses)
    if condition_met < 0:
      return
    schedule = {}
    drivers_type1 = []  # Водители первого типа
    drivers_type2 = []  # Водители второго типа
    last_route_end_time = {}  # Время завершения последнего маршрута для каждого водителя
    driver_start_time = {} # Время начала смены каждого водителя
    route_count = {}  # Счётчик маршрутов для второго типа водителей
    driver_shifts ={} # Словарь для хранения истории смен
    total_work_time = {} #Словарь для отслеживания рабочего времени
    max_work_time = {
        "T1": timedelta(hours=9),
        "T2": timedelta(hours=13)
    }
    had_lunch = {} # Словарь для отслеживания обеда водителей 1-го типа
    driver_work_days = {} #Рабочие дни водителей второго типа

    for day in range(7):
        shifts = {}  # Расписание для дня
        day_slots = get_time_slots(day, condition_met)

        for driver in drivers_type1:
          total_work_time[driver] = timedelta()
          last_route_end_time[driver] = None
          had_lunch[driver] = False

        for driver in drivers_type2:
          total_work_time[driver] = timedelta()
          last_route_end_time[driver] = None

        for slot in day_slots:
            assigned_driver = None

            # Определяем, какого типа водитель нужен
            is_weekend = day >= 5
            is_night_shift = "20:00" <= slot.strftime("%H:%M") or slot.strftime("%H:%M") < "08:00"

            if is_weekend or is_night_shift:
              assigned_driver = assign_driver(drivers_type2, slot, last_route_end_time,
                                              "T2", driver_shifts, total_work_time, max_work_time["T2"],
                                              route_duration, driver_work_days=driver_work_days, day=day)
            else:
              assigned_driver = assign_driver(drivers_type1, slot, last_route_end_time,
                                              "T1", driver_shifts, total_work_time, max_work_time["T1"],
                                              route_duration, had_lunch=had_lunch)

            if assigned_driver not in route_count:
                route_count[assigned_driver] = 0

            if assigned_driver not in driver_shifts:
              driver_shifts[assigned_driver] = []

            if assigned_driver not in driver_start_time:
              driver_start_time[assigned_driver] = slot

            # Определяем максимальную продолжительность смены для текущего водителя
            max_shift_hours = max_shift_hours_type1 if "T1" in assigned_driver else max_shift_hours_type2
            max_end_time = driver_start_time[assigned_driver] + timedelta(hours=max_shift_hours)

            # Проверяем, может ли водитель завершить маршрут до конца своей смены
            if slot + route_duration > max_end_time:
                replacing_driver = assign_driver(
                    drivers_type2 if "T2" in assigned_driver else drivers_type1,
                    slot, last_route_end_time,
                    "T2" if "T2" in assigned_driver else "T1",
                    driver_shifts,
                    total_work_time,
                    max_work_time["T2" if "T2" in assigned_driver else "T1"],
                    route_duration,
                    driver_work_days=driver_work_days, day=day
                )
                shifts[slot] = (replacing_driver, f"Рабочий день окончен! (Водитель {assigned_driver})")
                last_route_end_time[replacing_driver] = slot + route_duration
                driver_shifts[replacing_driver].append((day, slot, slot + route_duration, "Маршрут"))
                continue

            # Проверка на обед для водителей первого типа
            if "T1" in assigned_driver and 13 <= slot.hour < 15:
              if not had_lunch[assigned_driver]:
                last_end_time = last_route_end_time.get(assigned_driver)
                if is_driver_available(last_end_time, slot):
                    replacing_driver = assign_driver(drivers_type1,
                                                     slot, last_route_end_time,
                                                     "T1", driver_shifts,
                                                     total_work_time,
                                                     max_work_time["T1"],
                                                     route_duration, had_lunch)
                    shifts[slot] = (replacing_driver, f"Маршрут (Водитель {assigned_driver}, {slot.strftime('%H:%M')}-{(slot + timedelta(hours=1)).strftime('%H:%M')} -- обед)")
                    had_lunch[assigned_driver] = True
                    last_route_end_time[assigned_driver] = slot + timedelta(hours=1)
                    last_route_end_time[replacing_driver] = slot + route_duration
                    driver_shifts[assigned_driver].append((day, slot, slot + timedelta(hours=1), "Обед"))
                    driver_shifts[replacing_driver].append((day, slot, slot + route_duration, "Маршрут"))
                    continue

            # Проверка перерыва после двух маршрутов для второго типа
            if "T2" in assigned_driver:
                if last_route_end_time.get(assigned_driver) and slot >= last_route_end_time[assigned_driver]:
                    route_count[assigned_driver] += 1

                if route_count[assigned_driver] == 2:
                    last_end_time = last_route_end_time.get(assigned_driver)
                    last_route_end_time[assigned_driver] += timedelta(minutes=20)
                    end_break = last_route_end_time[assigned_driver]
                    start_break = end_break - timedelta(minutes=20)
                    if is_driver_available(last_end_time, slot):
                        replacing_driver = assign_driver(drivers_type2,
                                                         slot, last_route_end_time,
                                                         "T2", driver_shifts,
                                                         total_work_time,
                                                         max_work_time["T2"],
                                                         route_duration,
                                                         driver_work_days=driver_work_days,
                                                         day=day)
                        shifts[slot] = (replacing_driver, f"Маршрут (Водитель {assigned_driver}, {start_break.strftime('%H:%M')}-{end_break.strftime('%H:%M')} -- перерыв)")
                        driver_shifts[assigned_driver].append((day, start_break, end_break, "Перерыв"))
                        route_count[assigned_driver] = 0
                        last_route_end_time[replacing_driver] = slot + route_duration
                        driver_shifts[replacing_driver].append((day, slot, slot + route_duration, "Маршрут"))
                        continue

            # Назначаем слот
            shifts[slot] = (assigned_driver, "Маршрут")
            last_route_end_time[assigned_driver] = slot + route_duration
            driver_shifts[assigned_driver].append((day, slot, slot + route_duration, "Маршрут"))

        schedule[day] = shifts

    return schedule, drivers_type1, drivers_type2, driver_shifts

# Генерация расписания
schedule, drivers_type1, drivers_type2, driver_shifts = generate_schedule()

# Вывод расписания
print_schedule(schedule, drivers_type1, drivers_type2, driver_shifts)