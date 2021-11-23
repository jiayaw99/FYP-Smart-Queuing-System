import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

@anvil.server.callable
@anvil.tables.in_transaction
def do_update():
  row = app_tables.queue_table.search()
  for data in row:
    temp = data['Predicted waiting time']
    if temp!="No-show":
      temp = int(temp.split(' ')[0])+40
      my_dict = {"Predicted waiting time": str(temp) + " minutes"}
      app_tables.queue_table.get(Patient=data['Patient']).update(**my_dict)

  
