resistances = []

with open("bme680_gas_data.csv", 'r') as f:
    for line in f.readlines()[1:]:  # skip the header
        resistance = (line.split(",")[1].replace("\n", ''))
        resistances.append(int(resistance))

print(f"Average Resistance: {sum(resistances)/len(resistances)} Ohms")
print(f"Highest Resistance: {max(resistances[1:])} Ohms")