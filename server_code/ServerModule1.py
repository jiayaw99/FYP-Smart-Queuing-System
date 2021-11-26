import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

def getTime(current_clock):
  hour=int(current_clock/60) + 8
  minute=current_clock%60
  period=" am" if hour < 12 else " pm"
  if (hour>12):
    hour-=12
  return(str(hour)+"."+ ("0" + str(minute) if minute<10 else str(minute))+period) 

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
        my_dict = {"Predicted waiting time": str(temp) + " minutes" + " (" +getTime(temp)+")"}
        app_tables.queue_table.get(Patient=data['Patient']).update(**my_dict)
    else:
      skip+=1

      

  
