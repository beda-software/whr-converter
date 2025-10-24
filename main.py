from hl7apy.core import Message, Segment

# Create EVN Segment
evn = Segment("EVN")
evn.evn_1 = "A08"
evn.evn_2 = "198808181123"
evn.evn_3 = ""

# Create PID Segment
pid = Segment("PID")
pid.pid_1 = "12345"
pid.pid_2 = ""
pid.pid_3 = "34876^^^Local" # patient id
# pid.pid_5 = "Mouse^Mini^Marlene^^Dr"
pid.pid_5.pid_5_1 = 'Mouse3'
pid.pid_5.pid_5_2 = 'Mini4'
pid.pid_5.pid_5_3 = 'Marlene5'
pid.pid_5.pid_5_5 = 'Dr'
pid.pid_7 = "19890525000000+1000"
pid.pid_8 = "F"
pid.pid_10 = "9^^NHDDV10-000001"
pid.pid_11 = "123 Daisy Road^^Mouse Town^VIC^^^O"
pid.pid_13 = "07123456^PRN^PH^^61^07^123456~0444555666^^CP^^^^0444555666~^NET^Internet^mini.mouse@online.com"
pid.pid_14 = "07987654^WPN^PH^^61^07^987654"
pid.pid_16 = "0"

# Create PV1 Segment
pv1 = Segment("PV1")
pv1.pv1_1 = "1"
pv1.pv1_2 = "N"
pv1.pv1_8 = "0268203W^O'Brien^Chris^^^Dr^^^AUSHICPR^L^^^UPIN"

# Construct the message
msg = Message("ADT_A01")
# Create MSH Segment
msg.msh.msh_1 = "|"
msg.msh.msh_2 = "^~\\&"
msg.msh.msh_3 = "Beda EMR"
msg.msh.msh_4 = "The Practice"
msg.msh.msh_5 = "ViewPoint"
msg.msh.msh_6 = ""
msg.msh.msh_7 = "20171019102145+1000"
msg.msh.msh_8 = ""
msg.msh.msh_9 = "ADT^A08"
msg.msh.msh_10 = "34876" # Patient id
msg.msh.msh_11 = "P"
msg.msh.msh_12 = "2.3.1^AUS&&ISO^AS4700.2&&L"
msg.add(evn)
msg.add(pid)
msg.add(pv1)

# Output the HL7 message as a string
hl7_str = msg.to_er7()
print(hl7_str)
with open("file.txt", "w") as outfile:
        outfile.write(msg.to_er7())

