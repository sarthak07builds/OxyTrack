"""
Physics and Medical Gas Calculations for Oxygen Cylinders.
Applies Ideal Gas Law and Boyle's Law approximations with safety margins.
"""

def calculate_oxygen_volume(water_capacity_liters: float, pressure_bar: float) -> float:
    """
    Calculate the total available gaseous oxygen volume in Liters at atmospheric pressure (1 atm ~ 1.013 bar).
    Standard Medical Formula:
    Expanded Gas Volume (L) = Cylinder Water Capacity (L) * Pressure (Bar)
    """
    if water_capacity_liters <= 0 or pressure_bar <= 0:
        return 0.0
    return round(float(water_capacity_liters) * float(pressure_bar), 2)


def calculate_remaining_time(volume_liters: float, flow_rate_lpm: float, safe_residual_pressure_bar: float = 10.0, water_capacity_liters: float = 46.7) -> dict:
    """
    Calculates remaining duration in minutes and hours.
    Takes into consideration a safe residual pressure buffer (typically 10-15 bar) to avoid zero-flow collapse.
    """
    usable_volume = volume_liters
    if water_capacity_liters > 0 and safe_residual_pressure_bar > 0:
        residual_volume = safe_residual_pressure_bar * water_capacity_liters
        usable_volume = max(0.0, volume_liters - residual_volume)

    if flow_rate_lpm <= 0 or usable_volume <= 0:
        return {
            "minutes": 0.0,
            "hours": 0.0,
            "usable_volume_liters": round(usable_volume, 2),
            "formatted": "0h 0m"
        }

    total_minutes = usable_volume / flow_rate_lpm
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)

    return {
        "minutes": round(total_minutes, 2),
        "hours": round(total_minutes / 60, 2),
        "usable_volume_liters": round(usable_volume, 2),
        "formatted": f"{hours}h {minutes}m"
    }


def determine_cylinder_status(pressure_bar: float, max_pressure_bar: float, current_status: str) -> str:
    """
    Dynamically determines status based on pressure level.
    """
    if current_status == 'Maintenance':
        return 'Maintenance'
    
    percentage = (pressure_bar / max_pressure_bar) * 100.0 if max_pressure_bar > 0 else 0
    if percentage <= 10.0:
        return 'Depleted'
    return current_status
