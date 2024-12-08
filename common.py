from datetime import datetime, timedelta
import pandas as pd


def check_amount(route_duration, total_buses):
    """
    Вычисляет необходимое количество автобусов для поддержания заданного интервала между автобусами.
    Если количество необходимых автобусов больше, чем доступное количество, выводит предупреждение.
    """
    interval_normal = 10
    interval_peak = 5

    buses_needed_normal = int(route_duration / interval_normal) + 1
    buses_needed_peak = int(route_duration / interval_peak) + 1

    if buses_needed_normal > total_buses:
        print(f"Внимание! Необходимо как минимум {buses_needed_normal} автобусов для минимального покрытия интервалов.")
        return -1
    elif buses_needed_peak > total_buses:
      print(f"Внимание! Недостаточно автобусов для покрытия пиковых часов. Расписание будет сгенерировано без их учета.")
      return 0
    else:
        print(f"Для покрытия интервалов достаточно {total_buses} автобусов.")
        return 1

def get_time_slots(day_of_week, condition_met):
    """
    Генерирует временные слоты с 00:00 до 23:30.
    Интервалы:
    - Будни:
        - С 7:00 до 9:00 и с 17:00 до 19:00 — каждые 5 минут.
        - С 23:00 до 06:00 — каждые 30 минут.
        - Остальное время — каждые 10 минут.
    - Выходные:
        - С 23:00 до 06:00 — каждые 30 минут.
        - Остальное время — каждые 10 минут.
    """
    slots = []
    current_time = datetime.strptime("00:00", "%H:%M")
    end_time = datetime.strptime("23:30", "%H:%M")

    while current_time <= end_time:
        if day_of_week < 5:  # Будни
            if ("07:00" <= current_time.strftime("%H:%M") < "09:00" or
                "17:00" <= current_time.strftime("%H:%M") < "19:00") and condition_met > 0:
                interval = 5
            if ("07:00" <= current_time.strftime("%H:%M") < "09:00" or
                "17:00" <= current_time.strftime("%H:%M") < "19:00") and condition_met == 0:
                interval = 10
            elif "23:00" <= current_time.strftime("%H:%M") or current_time.strftime("%H:%M") < "06:00":
                interval = 30
            else:
                interval = 10
        else:  # Выходные
            if "23:00" <= current_time.strftime("%H:%M") or current_time.strftime("%H:%M") < "06:00":
                interval = 30
            else:
                interval = 10

        slots.append(current_time)
        current_time += timedelta(minutes=interval)

    return slots

def print_schedule(schedule, drivers_type1, drivers_type2, driver_shifts):
    """
    Выводит расписание и список водителей в виде таблицы.
    """
    print(f"Общее количество водителей первого типа: {len(drivers_type1)}")
    print(f"Общее количество водителей второго типа: {len(drivers_type2)}\n")

    # Форматируем расписание в таблицу
    print("Расписание по дням:")
    day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    schedule_data = []

    for day, shifts in schedule.items():
        for slot, (driver, shift_type) in shifts.items():
            schedule_data.append({
                "День": day_names[day],
                "Время": slot.strftime('%H:%M'),
                "Водитель": driver,
                "Тип смены": shift_type
            })

    schedule_df = pd.DataFrame(schedule_data)
    print(schedule_df.to_string(index=False))

    print("\nИстория работы водителей:")
    history_data = []
    for driver, shifts in driver_shifts.items():
        for shift in shifts:
            day, start, end, activity = shift
            history_data.append({
                "Водитель": driver,
                "День": day_names[day],
                "Начало": start.strftime('%H:%M'),
                "Конец": end.strftime('%H:%M'),
                "Деятельность": activity
            })

    history_df = pd.DataFrame(history_data)
    print(history_df.to_string(index=False))