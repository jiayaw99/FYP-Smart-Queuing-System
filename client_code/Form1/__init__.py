from ._anvil_designer import Form1Template
from anvil import *
import anvil.server
import time 


class Form1(Form1Template):
    
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.

  def data_grid_1_show(self, **event_args):
    """This method is called when the data grid is shown on the screen"""

    #count=0
    #while(True):
    predict = anvil.server.call('predict',2)
    row = DataRowPanel(item={'column_1':record[0],'column_2':record[1],
                                     'column_3':record[2],'column_4':record[3],
                                     'column_5':record[4],'column_6':round(record[5],2),
                                     'column_7':record[6]})
    self.data_grid_1.add_component(row)
      #count+=1
      #time.sleep(1)



