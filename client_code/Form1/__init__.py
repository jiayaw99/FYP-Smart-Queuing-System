from ._anvil_designer import Form1Template
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import time 
import random as rand
import math

disease =  {1: "A",2: "B",3: "C",4: "D",5: "E",6:"F"}
offset = 10  
adjustment = 0 # more predicted waiting time
adjustmentCount = 0
advance = 0 # less predicted waiting time
sleep = False

def RemovePatientWithDoctor(current_patient_with_doctor): # patient left
    if current_patient_with_doctor !=0 and current_patient_with_doctor[3]==0:
        index=current_patient_with_doctor[0]
        return index,True
    else:
        return 0,False

def CheckNoShow(arrival_index, current_waiting_patient): # patient not around
    random_noshow_rate=rand.randrange(20)/100   #20%
    index = current_waiting_patient[0][0]
    if rand.random() < random_noshow_rate and index!=arrival_index:
        return index
    else:
        return 0

def CallingForNoshow(noshow_trial):
    call_success_rate=rand.randrange(30)/100   #30%
    if rand.random() < call_success_rate and noshow_trial!=0:
        return False # patient came back on calling
    else:
        noshow_trial += 1
        return True  #not answering the call
      
def getTime(current_clock):
  hour=int(current_clock/60) + 8
  minute=current_clock%60
  period=" am" if hour < 12 else " pm"
  if (hour>12):
    hour-=12
  return(str(hour)+"."+ ("0" + str(minute) if minute<10 else str(minute))+period)                            
        
def assignNewPatientToQueue(doctor_number,new_patient,current_clock):
   global offset
   global adjustment
   result = anvil.server.call('predict',[doctor_number,new_patient[0],(-1 if new_patient[5]==-1 else 1),
                                        new_patient[6],new_patient[9]]) - offset + adjustment - advance
   if result < 0:
     result=0
   
   last_row=app_tables.queue_table.search(tables.order_by('Patient',ascending=False))
   if (len(last_row) > 0):
     last_row = last_row[0]
     if last_row['Predicted waiting time']!="No-show" and last_row['Predicted waiting time']!="ASAP" and new_patient[9] == 1:
       last_row_result = int(last_row['Predicted waiting time'].split(' ')[0])
       last_row_arrival = last_row['Arrival clock']
       current_predict = int(result)+current_clock
       last_row_predict =  last_row_result+last_row_arrival
       if current_predict <= last_row_predict:
          #print(str(last_row['Patient'])  +" predicted min: "+str(last_row_result) + " arrival : "+ str(last_row_arrival))
          print("patient " + str(new_patient[0]) + " offset +1" )
          result = result + last_row_predict - current_predict + 1
          offset -= 1


   predictResult = "" 
   if (new_patient[9]== 2 or new_patient[9] ==5):
      predictResult = "ASAP"
   else:
      predictResult = str(int(result)) + " minutes"+ " (" +getTime(current_clock+int(result))+")"

   my_dict={'Patient': new_patient[0],
            'Arrival time': getTime(current_clock),
            'Queue size when arrived': str(new_patient[6]),
            'Priority index': str(new_patient[9]),
            'Predicted waiting time': predictResult,
            'Arrival clock': current_clock}
  
   app_tables.queue_table.add_row(**my_dict)
   if new_patient[9]==2:
     anvil.server.call('delayPatientPriority2',doctor_number)

  
def servePatient(currentPatient,queue_panel,doctor_panel,current_clock):
  pop_row=app_tables.queue_table.get(Patient=currentPatient[0])
  my_dict={'Patient': pop_row['Patient'],
           'Time of being served': getTime(current_clock),
           'Actual waiting time': str(currentPatient[4]) + " minutes",
           'Predicted waiting time': pop_row['Predicted waiting time']}
  app_tables.doctor_table.add_row(**my_dict)
  
  global adjustmentCount
  global adjustment
  global advance
  
  if pop_row['Priority index'] == "1":
    temp = currentPatient[4]-int(pop_row['Predicted waiting time'].split(' ')[0])
    if(temp<0):
      print("delay: "+str(-temp) + " new patient adjustment "+str(temp))
      if adjustment != 0: 
        adjustment = 0
      else:
        advance = temp
      anvil.server.call('adjustmentDelay',-math.ceil(temp/2))
    elif(temp>=15):
      adjustmentCount+=1
      if(adjustmentCount == 3):
        adjustmentCount=0
        if advance !=0:
          advance = 0
        else:
          adjustment = 3
        print("adjustment: 3" )
        anvil.server.call('adjustmentDelay',3)
    else:
      adjustmentCount=0
    
    if(temp>20):
      print("above 20 minutes waited")
    
  pop_row.delete()
  queue_panel.items=app_tables.queue_table.search(tables.order_by("Priority index",ascending=False))
  doctor_panel.items=app_tables.doctor_table.search()
  
def getInstantServe(doctor_number,patient,current_clock,arrival_index,length):
  patient[6]=length
  Notification("New patient " + str(arrival_index) + " arrived  ",
  title="New Arrival",
  style="success",timeout=3).show()
  #print(patient)
  assignNewPatientToQueue(doctor_number,patient,current_clock)
  return True   

  
class Form1(Form1Template):
    

  def pause(self,**event_args):
    global sleep
    sleep = True
    pass

  def play(self,**event_args):
    global sleep
    sleep = False
    pass
  
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.

  
  def data_grid_1_show(self, **event_args):
    """This method is called when the data grid is shown on the screen"""
    #count=0
    self.button_pause.set_event_handler('click',self.pause)
    self.button_continue.set_event_handler('click',self.play)
    
    app_tables.doctor_table.delete_all_rows()
    app_tables.queue_table.delete_all_rows()
    doctors_number=[]
    for i in range(1): #doctor number in 30 days
      doctor_prob = rand.randrange(1000)
      doctor_prob = 5 if doctor_prob > 950 else (4 if doctor_prob > 500 else (3 if doctor_prob > 50 else 2))
      doctors_number.append(doctor_prob)
    largest_doctor = max(doctors_number)
    
    initial =[]

    for days in range(2): # 30 days
      doctor_number=doctors_number[days]
      clocksize = 600  # 10 hours (from 8 am to 6pm)
      current_clock = 0
      all_patient = []
      current_waiting_patient = []
      current_patient_with_doctor = [0]*doctor_number
      calling_patient = [0]*doctor_number
      emergency_patient = []
      emergency_record = []
      no_show_record = []
      doctor_idle_count = [0]*doctor_number
      noshow_trial = [0]*doctor_number
      calling = [False]*doctor_number
      index_noshow = [-1]*doctor_number
      Doctor_Status = [0]*doctor_number
      index = [0]*doctor_number

      self.doctor_number.text=str(doctor_number) + " doctors on call today"
      start_queue = int(doctor_number * (rand.randrange(20) + 80)/5)
      for i in range(start_queue):
        new_patient = [len(all_patient) + 1, rand.randrange(2), rand.randrange(10, 60),
                       anvil.server.call('getServiceTime',20,3), 0, -1,
                       start_queue,
                       rand.randrange(5)+1,rand.randrange(3)]  # patient index, gender, age, service time, waiting time, arrival time, queue size, disease type, disease condition

        priority=new_patient[2]/60+new_patient[7]+new_patient[8]
        new_patient.append(1 if priority < 7 else (2 if priority < 8 else 3)) # priority index
        all_patient.append(new_patient.copy())
        arrival_index = new_patient[0]
        current_waiting_patient.append(new_patient)
        current_waiting_patient.sort(key=lambda x: x[9],reverse=True)

      if current_clock == 0:
        result = anvil.server.call('initialPredict',doctor_number,current_waiting_patient)
        for i in range(len(current_waiting_patient)):
          result[i][0] -= 10
          if result[i][0] < 0:
            result[i][0]=0
            
          my_dict={'Patient': current_waiting_patient[i][0],
                   'Arrival time': "before 8.00 am",
                   'Queue size when arrived': str(current_waiting_patient[i][6]),
                   'Priority index': str(current_waiting_patient[i][9]),
                   'Predicted waiting time': str(int(result[i][0]))+" minutes" + " (" +getTime(int(result[i][0]))+")",
                   'Arrival clock': current_clock}
          app_tables.queue_table.add_row(**my_dict)
          

        self.queue_panel.items=app_tables.queue_table.search(tables.order_by("Priority index",ascending=False))

    #print('Clock size    Queue Size          Doctor 1 Status                      Doctor 2 Status                        Event')
      while current_clock < clocksize or any(v != 0 for v in current_patient_with_doctor) == True \
            or len(current_waiting_patient) != 0 or any(v != 0 for v in calling_patient) == True:

        self.clock.text=getTime(current_clock)                            
        
        skip_arrival=False
        arrival = False
        arrival_index = 0
        left = [False]*doctor_number
        emergency_index = 0
        emergency = False
        if (current_clock <= clocksize):
            random_arrival_rate = doctor_number * rand.randrange(10) / 100
        else:
            random_arrival_rate = 0
        if rand.random() < random_arrival_rate:
            new_patient = [len(all_patient) + 1, rand.randrange(2), rand.randrange(10, 60),
                           anvil.server.call('getServiceTime',20,3), 0, current_clock,
                           0, rand.randrange(5)+1,rand.randrange(3)]  # patient index, gender, age, service time, waiting time, arrival time, queue size
            priority = new_patient[2] / 60 + new_patient[7] + new_patient[8]
            new_patient.append(1 if priority < 7 else (2 if priority < 8 else 3))  # priority index
            all_patient.append(new_patient.copy())
            arrival = True
            arrival_index = new_patient[0]
            current_waiting_patient.append(new_patient)
            current_waiting_patient.sort(key=lambda x: x[9], reverse=True)
            
        #if rand.random() < 0.002:  # emergency case 
        if current_clock == 5:
            new_patient = [len(all_patient) + 1, rand.randrange(2), rand.randrange(10, 60),
                           anvil.server.call('getServiceTime',40,2), 0, current_clock, -1,
                           6,2,5]
            all_patient.append(new_patient.copy())
            emergency = True
            emergency_index = new_patient[0]
            emergency_patient.append(new_patient)
            emergency_record.append(emergency_index)
            
            Notification( "New emergency patient " + str(emergency_index) + " arrived  ",
            title="Emergency Arrival",
            style="danger",timeout=3).show()
            assignNewPatientToQueue(doctor_number,all_patient[emergency_index-1],current_clock)
            self.queue_panel.items=app_tables.queue_table.search(tables.order_by("Priority index",ascending=False))

        for i in range(len(current_patient_with_doctor)):
            index[i], left[i] = RemovePatientWithDoctor(current_patient_with_doctor[i])
            if (left[i]):
                all_patient[index[i] - 1][4] = current_patient_with_doctor[i][4]
                current_patient_with_doctor[i] = 0

        if len(emergency_patient) != 0:
            for i in range(len(current_patient_with_doctor)):
                if current_patient_with_doctor[i]==0:
                    servePatient(emergency_patient[0],self.queue_panel,self.patient_with_doctor,current_clock)
                    
                    current_patient_with_doctor[i] = emergency_patient.pop(0)
                    break

        for i in range(doctor_number):
            if calling[i]:
                calling[i] = CallingForNoshow(noshow_trial[i])
                if (calling[i] and noshow_trial[i] == 5):
                    all_patient[index_noshow[i] - 1][3] = 0  # service time equal to 0 if no show
                    all_patient[index_noshow[i] - 1][4] = calling_patient[i][4]
                    calling_patient[i]=0
                    no_show_record.append(index_noshow[i])
                    if len(current_waiting_patient) > 0 and current_patient_with_doctor[i] == 0:
                      if arrival and len(current_waiting_patient)==1:
                          skip_arrival=getInstantServe(doctor_number,all_patient[arrival_index-1],current_clock,arrival_index,len(current_waiting_patient))
                          self.queue_panel.items=app_tables.queue_table.search(tables.order_by("Priority index",ascending=False))

                      elif arrival and current_waiting_patient[0][0] == arrival_index:
                          skip_arrival=getInstantServe(doctor_number,all_patient[arrival_index-1],current_clock,arrival_index,len(current_waiting_patient))
                          self.queue_panel.items=app_tables.queue_table.search(tables.order_by("Priority index",ascending=False))
                      
                      servePatient(current_waiting_patient[0],self.queue_panel,self.patient_with_doctor,current_clock)

                      current_patient_with_doctor[i] = current_waiting_patient.pop(0)
                elif calling[i] == False:
                    noshow_trial[i] = 0
                    if current_patient_with_doctor[i] == 0:
                        servePatient(calling_patient[i],self.queue_panel,self.patient_with_doctor,current_clock)

                        current_patient_with_doctor[i] = calling_patient[i]
                    else:
                        current_waiting_patient.insert(0, calling_patient[i])
                    calling_patient[i]=0

            elif len(current_waiting_patient) != 0:
                if current_patient_with_doctor[i] == 0:
                    index_noshow[i] = CheckNoShow(arrival_index, current_waiting_patient)  ##prevent no-show happen at the arrival time
                    if (index_noshow[i]) != 0:
                        calling[i] = CallingForNoshow(noshow_trial[i])
                        calling_patient[i]=current_waiting_patient.pop(0)
                        
                    else:
                        if arrival and len(current_waiting_patient)==1:
                          skip_arrival=getInstantServe(doctor_number,all_patient[arrival_index-1],current_clock,arrival_index,len(current_waiting_patient))
                          self.queue_panel.items=app_tables.queue_table.search(tables.order_by("Priority index",ascending=False))

                        elif arrival and current_waiting_patient[0][0] == arrival_index:
                          skip_arrival=getInstantServe(doctor_number,all_patient[arrival_index-1],current_clock,arrival_index,len(current_waiting_patient))
                          self.queue_panel.items=app_tables.queue_table.search(tables.order_by("Priority index",ascending=False))
      
                        servePatient(current_waiting_patient[0],self.queue_panel,self.patient_with_doctor,current_clock)

                        current_patient_with_doctor[i] = current_waiting_patient.pop(0)

        if len(current_waiting_patient) != 0:
            for patient in current_waiting_patient:
                patient[4] += 1
        for i in range(len(calling_patient)):
            if calling_patient[i] != 0:
                calling_patient[i][4] += 1
        if len(emergency_patient) != 0:
            for patient in emergency_patient:
                patient[4] += 1

        for i in range(len(current_patient_with_doctor)):
            if current_patient_with_doctor[i] != 0:
                current_patient_with_doctor[i][3] -= 1

        for i in range(doctor_number):
            Doctor_Status[i] = "Occupied with patient " + str(current_patient_with_doctor[i][0]) if current_patient_with_doctor[i] != 0 else str("Idle")
            if (Doctor_Status[i] == "Idle"):
                doctor_idle_count[i] += 1

        if arrival and not skip_arrival:
            all_patient[arrival_index-1][6]=len(current_waiting_patient)
            Notification("New patient " + str(arrival_index) + " arrived  ",
            title="New Arrival",
            style="success",timeout=3).show()
            
            assignNewPatientToQueue(doctor_number,all_patient[arrival_index-1],current_clock)

            self.queue_panel.items=app_tables.queue_table.search(tables.order_by("Priority index",ascending=False))

        if emergency:
            anvil.server.call('delayPatientEmergency',doctor_number)
            
            self.queue_panel.items=app_tables.queue_table.search(tables.order_by("Priority index",ascending=False))
            #To be edit, all patient +40 minutes
        for i in range(doctor_number):
            if left[i]:
              Notification("Patient " + str(index[i]) + " left  ",
              title="Patient Left",
              style="success",timeout=3).show()
              
              app_tables.doctor_table.get(Patient=index[i]).delete()
              self.patient_with_doctor.items=app_tables.doctor_table.search()
              
            if noshow_trial[i] < 5 and calling[i] == True:
              noshow_trial[i] += 1
              if(noshow_trial[i]==1):
                Notification("Calling for Patient " + str(index_noshow[i]),
                title="Calling for Patient",
                style="warning",timeout=3).show()
            elif noshow_trial[i] == 5 and index_noshow[i] != 0 and calling[i]:
                noshow_trial[i] = 0
                calling[i] = False
                calling_patient[i]=0
                Notification("Patient " + str(index_noshow[i]) + " no show ",
                title="Patient No-show",
                style="warning",timeout=3).show()  
                
                my_dict={"Predicted waiting time": "No-show"}
                app_tables.queue_table.get(Patient=index_noshow[i]).update(**my_dict)
                anvil.server.call('reducePredictedTime',doctor_number)

                self.queue_panel.items=app_tables.queue_table.search()
                #self.queue_panel.raise_event_on_children("x-noshow-event")
                #To be edit,change to red text and remain in list
                
        current_clock += 1
        if len(current_waiting_patient)/doctor_number >= 10 and current_clock<clocksize and current_clock > 450:  # do not accept patient anymore if too much queue near the closing hour
            clocksize = 450
        elif len(current_waiting_patient)/doctor_number >= 5 and current_clock<clocksize and current_clock > 550:  # do not accept patient anymore if too much queue near the closing hour
            clocksize = 550
        
        time.sleep(0.5)

        while(sleep):
          time.sleep(0.5)
          
        





