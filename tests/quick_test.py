from src.lmr_coordinate_calculator import LMRCoordinateCalculator

calc = LMRCoordinateCalculator()
coords = calc.calculate_coordinates(1067)

print("修正後の座標:")
print(f"L: X={coords['L_X']}, Y={coords['L_Y']}")
print(f"M: X={coords['M_X']}, Y={coords['M_Y']}")
print(f"R: X={coords['R_X']}, Y={coords['R_Y']}")
