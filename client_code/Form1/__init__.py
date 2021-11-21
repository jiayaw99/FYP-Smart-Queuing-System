from ._anvil_designer import Form1Template
from anvil import *
import anvil.server
import time 
import random as rand
disease =  {1: "A",2: "B",3: "C",4: "D",5: "E",6:"F"}

def RemovePatientWithDoctor(current_patient_with_doctor):
    if current_patient_with_doctor !=0 and current_patient_with_doctor[3]==0:
        index=current_patient_with_doctor[0]
        return index,True
    else:
        return 0,False

def CheckNoShow(arrival_index, current_waiting_patient):
    random_noshow_rate=rand.randrange(20)/100  #15
    index = current_waiting_patient[0][0]
    if rand.random() < random_noshow_rate and index!=arrival_index:
        return index
    else:
        return 0

def CallingForNoshow(noshow_trial):
    call_success_rate=rand.randrange(30)/100   #30
    if rand.random() < call_success_rate and noshow_trial!=0:
        return False
    else:
        noshow_trial += 1
        return True  #not answering the call

class Form1(Form1Template):
    
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.

  def data_grid_1_show(self, **event_args):
    """This method is called when the data grid is shown on the screen"""

    #count=0
    doctors_number=[]
    for i in range(1): #doctor number in 30 days
      doctor_prob = rand.randrange(1000)
      doctor_prob = 5 if doctor_prob > 950 else (4 if doctor_prob > 500 else (3 if doctor_prob > 50 else 2))
      doctors_number.append(doctor_prob)
    largest_doctor = max(doctors_number)
    
    initial =[]

    for days in range(1): # 30 days
      doctor_number=doctors_number[days]
      clocksize = 480  # 8 hours
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
      start_queue = int(doctor_number * (rand.randrange(20) + 30)/5)
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
      
      if current_clock ==0:
        for i in range(len(current_waiting_patient)):
          #self.current_queue.items=
           result = anvil.server.call('predict',[[doctor_number,current_waiting_patient[i][0],
                                                 (-1 if current_waiting_patient[i][5]==-1 else 1),
                                                 current_waiting_patient[i][6],
                                                 current_waiting_patient[i][9]]])
           row = DataRowPanel(item={'column_1':current_waiting_patient[i][0],
                                    'column_2':"before 8.00 am",
                                    'column_3':current_waiting_patient[i][6],
                                    'column_4':current_waiting_patient[i][9],
                                    'column_5':result})
      #self.data_grid_1.add_component(row)
                                   
           self.data_grid_1.add_component(row)

    #print('Clock size    Queue Size          Doctor 1 Status                      Doctor 2 Status                        Event')
      while current_clock < clocksize or any(v != 0 for v in current_patient_with_doctor) == True \
            or len(current_waiting_patient) != 0 or any(v != 0 for v in calling_patient) == True:
        hour=int(current_clock/60)
        minute=current_clock%60
        if (hour>12):
          hour-=12 
        self.clock.text=str(8+hour)+"."+ ("0" + str(minute) if minute<10 else str(minute))+(" pm" if hour>4 else " am")                            
        current_clock += 1
        
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

        if rand.random() < 0.002:  # emergency case
            new_patient = [len(all_patient) + 1, rand.randrange(2), rand.randrange(10, 60),
                           anvil.server.call('getServiceTime',40,2), 0, current_clock, -1,
                           6,2,5]
            all_patient.append(new_patient.copy())
            emergency = True
            emergency_index = new_patient[0]
            emergency_patient.append(new_patient)
            emergency_record.append(emergency_index)

        for i in range(len(current_patient_with_doctor)):
            index[i], left[i] = RemovePatientWithDoctor(current_patient_with_doctor[i])
            if (left[i]):
                all_patient[index[i] - 1][4] = current_patient_with_doctor[i][4]
                current_patient_with_doctor[i] = 0

        if len(emergency_patient) != 0:
            for i in range(len(current_patient_with_doctor)):
                if current_patient_with_doctor[i]==0:
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
                        current_patient_with_doctor[i] = current_waiting_patient.pop(0)
                elif calling[i] == False:
                    noshow_trial[i] = 0
                    if current_patient_with_doctor[i] == 0:
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

        if arrival:
            all_patient[arrival_index-1][6]=len(current_waiting_patient)
            Notification("New patient " + str(arrival_index) + " arrived  ",
             title="New Arrival",
             style="success").show()
        if emergency:
            Notification( "New emergency patient " + str(emergency_index) + " arrived  ",
             title="Emergency Arrival",
             style="danger").show()
        for i in range(doctor_number):
            if left[i]:
              Notification("Patient " + str(index[i]) + " left  ",
              title="Patient Left",
              style="success").show()
            if noshow_trial[i] < 5 and calling[i] == True:
              noshow_trial[i] += 1
              Notification("Calling for Patient " + str(index_noshow[i]) + " " + str(noshow_trial[i]) + " time(s) ",
              title="Calling for Patient",
              style="warning").show()
            elif noshow_trial[i] == 5 and index_noshow[i] != 0 and calling[i]:
                noshow_trial[i] = 0
                calling[i] = False
                calling_patient[i]=0
                Notification("Patient " + str(index_noshow[i]) + " no show ",
                title="Patient No-show",
                style="warning").show()  

        if len(current_waiting_patient) > 10 and current_clock > 360:  # do not accept patient anymore if too much queue near the closing hour
            clocksize = 360
        time.sleep(1)


    #while(True):
      #row = DataRowPanel(item={'column_1':record[0],'column_2':record[1],
                                     #'column_3':record[2],'column_4':record[3],
                                     #'column_5':record[4],'column_6':round(record[5],2),
                                    # 'column_7':record[6]})
      #self.data_grid_1.add_component(row)
      #count+=1
      #time.sleep(1)



