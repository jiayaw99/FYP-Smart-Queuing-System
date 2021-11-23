from ._anvil_designer import RowTemplate3Template
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

class RowTemplate3(RowTemplate3Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.set_event_handler("x-noshow-event", self.change_red)
    
  def change_red(self, **event_args):
    if self.label_4.text == "No-show":
      self.label_4.foreground="#f51919"
