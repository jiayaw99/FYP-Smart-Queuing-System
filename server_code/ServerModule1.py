import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

@anvil.server.callable
@tables.in_transaction
def delay_Patient(doctor_number):
  row = app_tables.queue_table.search(tables.order_by("Priority index",ascending=False))
  skip = 0
  for data in row:
    if skip >= 1:
      temp = data['Predicted waiting time']
      if temp!="No-show":
        temp = int(temp.split(' ')[0])+ int(50/doctor_number)
        my_dict = {"Predicted waiting time": str(temp) + " minutes"}
        app_tables.queue_table.get(Patient=data['Patient']).update(**my_dict)
    else:
      skip+=1

  
