from ._anvil_designer import Form1Template
from anvil import *
import anvil.server

class Form1(Form1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.
    

  def data_grid_1_show(self, **event_args):
    """This method is called when the data grid is shown on the screen"""
    iris_category = anvil.server.call('simulation')

    pass


