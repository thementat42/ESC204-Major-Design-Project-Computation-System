# ___________________________________________________________________
# LINKED LIST REPRESENTATION
# Define a module
# class module:
#     def __init__(self, id, temperature, humidity, pressure, gas, light, latitude, longitude):
#         self.id = id
#         self.temperature = temperature
#         self.humidity = humidity
#         self.pressure = pressure
#         self.gas = gas
#         self.light = light
#         self.coords = (latitude, longitude)
#         self.next = None # Allows modules to be iterated through via a linked list

# # Define a system of modules        
# class system:
#     def __init__(self):
#         self.start = None
    
#     def size(self):
#         '''Returns the number of modules in the system'''

#         if self.start == None:
#             return 0

#         num = 0 # The number of modules
#         cur = self.start
#         while cur:
#             while cur.next != None:
#                 num += 1
#                 cur = cur.next
        
#         return num

#     def values(self, id):
#         '''Returns the values of a given module of the specified index'''

#         if self.start == None:
#             return "System Empty"
        
#         # Check the size of the system to make sure id not out of range
#         num = 0 # The number of modules
#         cur = self.start
#         while cur:
#             while cur.next != None:
#                 num += 1
#                 cur = cur.next
        
#         if id > num:
#             return "Invalid Index"
        
#         # Find the module at the specified index
#         cur = self.start
#         for i in range(id - 1):
#             cur = cur.next

#         return cur.coords, cur.temperature, cur.humidity, cur.pressure, cur.gas, cur.light
    
#     def add_module(self, new_module):
#         '''Adds a new module'''

#         # Check the size of the system 
#         num = 0 # The number of modules
#         cur = self.start
#         while cur:
#             while cur.next != None:
#                 num += 1
#                 cur = cur.next
        
#         # new_module = module((num + 1), temperature, humidity, pressure, gas, light, latitude, longitude)
#         if self.start == None:
#             self.start = new_module
        
#         # Create a new module to add to the system
#         cur = self.start
#         for i in range(num - 1):
#             cur = cur.next
#         cur.next = new_module
    
#     def update_module(self, id, temperature, humidity, pressure, gas, light):
#         '''Updates module values for display'''

#         if id == 1:
#             self.start.temperature = temperature
#             self.start.humidity = humidity
#             self.start.pressure = pressure
#             self.start.gas = gas
#             self.start.light = light

#         else:
#             cur = self.start
#             for i in range(id):
#                 cur = cur.next
#             cur.temperature = temperature
#             cur.humidity = humidity
#             cur.pressure = pressure
#             cur.gas = gas
#             cur.light = light

# def extract_values(string):
#     '''Exctract data from a json string and create a module out of it'''
#     set = json.loads(string)

#     id = set["id"]
#     temperature = set["temperature"]
#     humidity = set["humidity"]
#     pressure = set["pressure"]
#     gas = set["gas"]
#     light = set["light"]
#     latitude = set["latitude"]
#     longitude = set["longitude"]

#     mod = module(id, temperature, humidity, pressure, gas, light, latitude, longitude)

#     return mod

# def create_system(list):
#     '''Takes in a list of json strings and makes a linked list (system) of modules out of them'''
#     sys = system()
#     for string in list:
#         new_mod = extract_values(string)
#         sys.add_module(new_mod)
#     return sys