#!/tool/pandora64/bin/python3.10

#demo command:  python cross_cov.py -i intf_CLIENT_SHUB.nbif_chtgfx.log -clk clock_info.log -o save.log

#this script is used to generate coverage for one test
#input is intf*log and clock_info.log
#output is csv file (option)
#output is 2d array by default

import os,sys
import subprocess
import re

#use-defined module
import get_trans_type as TransType
import csv_handle as CsvH

#global define
type_f = ""
chk_file  = ""
based_on_cycle=1 # check cross coverage based on cycle nubmers or based on realtime

collect_output =1 #collect output logtrans to generate AllTransObjs[$]
collect_input = 1 #collect input logtrans to generate AllTransObjs[$]
collect_cmpl = 0   #collect completion logtrans CMPLT CMPLTDto generate AllTransObjs[$]
check_output = 1 #check cross coverage of output trans
check_input = 1 #check cross coverage of input trans
check_cmpl = 0 #check cross coverage of cmplt/cmplt_d
dbg_en = 0 #log more debug info

typelevel = "L3Type" # .L1Type=NP/P L2Type=MEM_RD ATOMICE MEW_WR (the type we can get directly from intf.log L3Type=FLUSH FETCH_ADD MEM_WR (the type we can decoder from the translog)
cross_with_all_types = 0
trans_dbg_name = "trans_info.dbg"
trans_dbg = open(trans_dbg_name,'w')


#temp array for cross coverage check same clock domain based on cycles.
#per clock

crossCycles = 1
#"Trans1""Trans2"  HDP_WR HDP_FLUSH CPF_WR
#"HDP_FLUSH" may be reported as "HDP_RD"
#HDP_FLUSH == HDP_RD && DATA=0
#
#
crossTime = 20000

class LogTrans:
    'class for a trans in intf.log'


    def __init__(self, RawTxt, clkarr, userarr):
        #basic name info
        self.RawTxt=RawTxt
        self.ClkInfoArr=clkarr
        self.UserDefInfoArr=userarr
        self.GetTransInfo()
        

#Trans format in bif_module_transactions
#### info_str[i] = $psprintf("%11s %9s %10t %1s %1s %10s %4s %1s %2s %8s %4s %4s %1s %18s %2s %12s %4s %5s %35s %3s %1s %0s", intf_str, clk_str,
####                        $realtime,dir_str,portid_str,trans_type_str10,rid_str,vf_str, vf_id_str, unit_axi_id_str,tag_str,cpldid_str,chain_str,addr_str,addr_align_str,
####                        sts_msg_str,be_str[i],len_str,pdata_str[i],data_align_str,ep_str,user_str);
##[0:10]11[12:20]21[22]23[24]25
    def GetTransInfo(self):
        #lineinfo = self.RawTxt.split()
        port_len = 15 #before is 11, some port like ACP_DOORBELL is longer
        clk_len = 10
        start_time_len = 11
        finish_time_len = 11
        dir_len = 2
        portid_len = 3
        #portid_len = 3
        transtype_len = 16
        #transtype_len = 10
        req_bus_num_len = 6
        reqid_len= 5
        vf_len = 2
        vfid_len = 3
        #axiid_len =9
        axiid_len = 10
        tag_len = 5
        cpldid_len=5
        chain_len = 2
        addrh_len = 10
        addrl_len = 10
        addralign_len = 3
        cmd_len = 13
        be_len = 5
        index_len = 6
        data_len = 9
        data_finish_time_len = 11
        data_bus_num_len = 5
        data_align_len = 4
        ep_len = 2
        total_len = len(self.RawTxt)
        userbit_len = total_len-172
        self.SubIPName = ""

        start_len = 0
        end_len = port_len

        self.PortName=self.RawTxt[start_len : end_len].strip() #[0:11]
        start_len = end_len
        end_len  = end_len + clk_len
        self.ClkName=self.RawTxt[start_len : end_len].strip() #[11:22]
        start_len = end_len
        end_len  = end_len + start_time_len
        self.StartTimestamp=self.RawTxt[start_len : end_len].strip() #[22:33]
        start_len = end_len
        end_len  = end_len + finish_time_len
        self.FinishTimestamp=int(self.RawTxt[start_len : end_len].strip()) #[22:33]
        start_len = end_len
        end_len  = end_len + dir_len
        self.Direction = self.RawTxt[start_len : end_len].strip() #[33:35]
        start_len = end_len
        end_len  = end_len + portid_len #[35:37]
        self.PortID = self.RawTxt[start_len : end_len].strip()
        start_len = end_len
        end_len  = end_len + transtype_len
        self.Type = self.RawTxt[start_len : end_len].strip() #[37:48]
        start_len = end_len
        end_len  = end_len + req_bus_num_len
        self.ReqBusNum = self.RawTxt[start_len : end_len].strip() #[48:53]
        start_len = end_len
        end_len  = end_len + reqid_len
        self.ReqID = self.RawTxt[start_len : end_len].strip() #[48:53]
        start_len = end_len
        end_len  = end_len + vf_len 
        self.VF = self.RawTxt[start_len : end_len].strip() #[53:55]
        start_len = end_len
        end_len  = end_len + vfid_len
        self.VFID = self.RawTxt[start_len : end_len].strip() #[55:58]
        start_len = end_len
        end_len  = end_len + axiid_len #[58:67]
        self.AxiID = self.RawTxt[start_len : end_len].strip()
        start_len = end_len
        end_len  = end_len + tag_len #[67:72]
        self.TagID = self.RawTxt[start_len : end_len].strip()
        start_len = end_len
        end_len  = end_len + cpldid_len #[72:77]
        self.CpldID = self.RawTxt[start_len : end_len].strip()
        start_len = end_len
        end_len  = end_len + chain_len #[77:79]
        self.Chain = self.RawTxt[start_len : end_len].strip()
        start_len = end_len
        end_len  = end_len + addrh_len #[79:89]
        self.AddrH =  self.RawTxt[start_len : end_len].strip()
        start_len = end_len
        end_len  = end_len + addrl_len
        self.AddrL =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len
        end_len = end_len + addralign_len
        self.AddrAlign =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len
        end_len = end_len + cmd_len
        self.CMD =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len
        end_len = end_len + be_len
        self.BE =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len
        end_len = end_len + index_len
        self.Index =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len
        end_len  = end_len + data_finish_time_len
        self.DataFinishTime = self.RawTxt[start_len : end_len].strip() #[48:53]
        start_len = end_len
        end_len  = end_len + data_bus_num_len
        self.DataBusNum = self.RawTxt[start_len : end_len].strip() #[48:53]
        start_len = end_len
        end_len = end_len + data_len
        self.Data4 =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len
        end_len = end_len + data_len
        self.Data3 =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len
        end_len = end_len + data_len
        self.Data2 =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len
        end_len = end_len + data_len
        self.Data1 =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len
        end_len = end_len + data_align_len
        self.DataAlign =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len
        end_len = end_len + ep_len
        self.EP =  self.RawTxt[start_len : end_len].strip() #[89:98]
        #start_len = end_len
        #end_len = end_len + userbit_len
        #self.AddrL =  self.RawTxt[start_len : end_len].strip() #[89:98]
        start_len = end_len 
        end_len  = total_len
        self.UserBit =  self.RawTxt[start_len : end_len].strip() #[89:98]       #start_len = end_len
        #end_len = end_len + userbit_len
        #self.AddrL =  self.RawTxt[start_len : end_len].strip() #[89:98]

        self.ClkPeriod = float(self.ClkInfoArr[self.ClkName]) * 1000
        self.ClkCycles = int(self.FinishTimestamp // self.ClkPeriod)
        self.Data=""
        self.UserDefType = "NA"
        #self.L1Type=NP/P
        #self.L2Type=MEM_RD ATOMICE MEW_WR
        #self.L3Type=FLUSH FETCH_ADD MEM_WR
        #if (lineinfo[14] != "--------"):
        for n in range(len(self.UserDefInfoArr)):
            if((str(self.FinishTimestamp) == str(self.UserDefInfoArr[n][0])) and (str(self.AxiID) == str(self.UserDefInfoArr[n][1]))):
                self.UserDefType = self.UserDefInfoArr[n][2]      #get user_def_type in terms of realtime and unit_id or axi_id
                break
        self.L1Type = TransType.get_transtype(self, "L1Type")
        self.L2Type = TransType.get_transtype(self, "L2Type")
        self.L3Type = TransType.get_transtype(self, "L3Type")
        if(dbg_en==3):
            if(self.UserDefType!="NA"):
                print self.L3Type
            #if(self.L3Type!="NA"):
                #print self.FinishTimestamp,self.L3Type

    def AddDataLine(self,DataLine):
        self.Data = self.Data + DataLine # this need to be updated

       # matchObj=re.search(r'^\s+(\w+)\s',self.RawTxt)
       # if matchObj:
       #     self.PortName=matchObj.group(1)
       # else:
       #     self.PortName="null"

    def TransPrint(self):
#        print "Trans info:\n"
#        print "    PortName : ", self.PortName, "\n"
#        print "    Direction : ", self.Direction, "\n"
#        print "    Type     : ", self.Type, "\n"
#        print "    L1Type     : ", self.L1Type, "\n"
#        print "    L2Type     : ", self.L2Type, "\n"
#        print "    L3Type     : ", self.L3Type, "\n"
#        print "    AddrH   : ", self.AddrH, "\n"
#        print "    AddrL   : ", self.AddrL, "\n"
#        print "    VF     : ", self.VF, "\n"
#        print "    ClkName  : ", self.ClkName, "\n"
#        print "    ClkPeriod   : ", self.ClkPeriod, "\n"
#        print "    Timestamp: ", self.Timestamp, "\n"
#        print "    ClkCycles   : ", self.ClkCycles, "\n"
#        print "    UserDefType  : ", self.UserDefType, "\n"
#        print "    Data     : ", self.Data, "\n"

        trans_dbg.write("Trans info:\n")
        trans_dbg.write("    PortName : "+str(self.PortName)+"\n")
        trans_dbg.write("    L3Type     : "+str(self.L3Type)+"\n")
        trans_dbg.write("    UserDefType  : "+str(self.UserDefType)+"\n")

    def TransLineDisplayPrint(self):
        trans_line = "{:>7}{:>15}{:>10}{:>11}{:>11}{:>2}{:>2}{:>15}{:>5}{:>2}{:>3}{:>11}{:>5}{:5}{:2}{:>10}{:>10}{:>3}{:>13}{:>5}{:>6}{:>11}{:>5}{:>9}{:>9}{:>9}{:>9}{:>4}{:>2}{}".format\
        (self.SubIPName,self.PortName,self.ClkName,self.StartTimestamp,self.FinishTimestamp,self.Direction,self.PortID,self.Type,self.ReqID,self.VF,self.VFID,self.AxiID,self.TagID,self.CpldID,\
        self.Chain,self.AddrH,self.AddrL,self.AddrAlign,self.CMD,self.BE,self.Index,self.DataFinishTime,self.DataBusNum,self.Data4,self.Data3,self.Data2,self.Data1,self.DataAlign,self.EP,self.UserBit)
        return trans_line

    def TransLineParsePrint(self):
        trans_line = "{:>15}{:>10}{:>11}{:>11}{:>2}{:>2}{:>15}{:>5}{:>2}{:>3}{:>11}{:>5}{:5}{:2}{:>10}{:>10}{:>3}{:>13}{:>5}{:>6}{:>11}{:>5}{:>9}{:>9}{:>9}{:>9}{:>4}{:>2}{}".format\
        (self.PortName,self.ClkName,self.StartTimestamp,self.FinishTimestamp,self.Direction,self.PortID,self.Type,self.ReqID,self.VF,self.VFID,self.AxiID,self.TagID,self.CpldID,\
        self.Chain,self.AddrH,self.AddrL,self.AddrAlign,self.CMD,self.BE,self.Index,self.DataFinishTime,self.DataBusNum,self.Data4,self.Data3,self.Data2,self.Data1,self.DataAlign,self.EP,self.UserBit)
        return trans_line

def get_clkinfo_from_file(filename):
    global dbg_en
    ClkInfoArr={}
    with open(filename, 'r') as f_r :
        clk_lines= f_r.readlines()

    for i in range (0,len(clk_lines)):
        clk_info = clk_lines[i].split()
        clk_name = clk_info[0]
        ClkInfoArr[clk_name] = clk_info[1]
    if (dbg_en == 1):
        print "Clock Info:", ClkInfoArr
    f_r.close()
    return ClkInfoArr

def get_user_def_info_from_file(filename):
    global dbg_en
    UserDefInfoArr = []
    with open(filename,'r') as f_r:
        user_def_lines = f_r.readlines()
    for i in range(len(user_def_lines)):
        UserDefInfoArr.append(user_def_lines[i].split())   #realtime unit_id/axi_id user_def_type
    if(dbg_en==1):
        print "User Define Info:",UserDefInfoArr
    f_r.close()
    return UserDefInfoArr


def read_trans_from_file(filename, clkarr, userarr):
    global dbg_en
    AllLogTransObjs=[]

    if (dbg_en ==1):
        print "get transinfo from file --", filename
    with open(filename, 'r') as f_r :
        saved_log_lines= f_r.readlines()

    header_line_found=0
    for i in range (0,len(saved_log_lines)):
        if (dbg_en ==2):
            print "DEBUG--loglines ---", saved_log_lines[i]
        #search header line
        if header_line_found<2:
            matchObj=re.search(r'^-----',saved_log_lines[i])
            if matchObj:
                header_line_found= header_line_found+1

        #after 2 header lines found, it's trans started
        else: 
            if (saved_log_lines[i][0:15].strip() != "unknown"): 
                if(saved_log_lines[i][0:15].strip() != ""):  #if portname is not empty, then this is a first line of a trans
                    linelen = len(saved_log_lines[i])
                    if (dbg_en ==2):
                        print "DEBUG--loglines length ---", str(linelen)
                    if (linelen > 50) : #sometimes last line of intflog may not be complete. at least it contains basic infromation, port/clock/transtype
                        iTrans=LogTrans(saved_log_lines[i], clkarr, userarr)
                        if (need_log(iTrans)):
                            AllLogTransObjs.append(iTrans)
                #else:
                    #AllLogTransObjs[len(AllLogTransObjs)-1].AddDataLine(saved_log_lines[i]) #add this data line to last trans

    #print "Display all trans:"
    if (dbg_en == 2):
        for i in range (0,len(AllLogTransObjs)):
            AllLogTransObjs[i].TransPrint()       
    print AllLogTransObjs
    f_r.close()
    print len(AllLogTransObjs)
    return AllLogTransObjs

def need_log(logtrans):
   # print "needlog: -collect_input=", collect_input 
   # print "needlog: -collect_output=", collect_output

    needlog = 0

    if (TransType.is_output(logtrans) and (collect_output == 1)):
        needlog = 1
    #    print "Debug: needlog output ", logtrans.PortName, logtrans.Type 
    elif (TransType.is_input(logtrans) and (collect_input == 1)):
        needlog = 1
    #    print "Debug: needlog input ", logtrans.PortName, logtrans.Type 

    elif (TransType.is_cmpl(logtrans) and (collect_cmpl == 1)):
        needlog = 1
    else :
        needlog = 0

    #if(TransType.is_level_sig_deasrt(logtrans)):
    #    needlog = 0
    return needlog


def need_check(logtrans):

    needchk = 0

    if (need_log(logtrans)==0):
        needchk = 0
    elif (TransType.is_output(logtrans) and (check_output == 1)):
        needchk = 1
        #print "Debug: needchk output ", logtrans.PortName, logtrans.Type 
    elif (TransType.is_input(logtrans) and (check_input == 1)):
        needchk = 1
        #print "Debug: needchk input ", logtrans.PortName, logtrans.Type 
    elif (TransType.is_cmpl(logtrans) and (check_cmpl == 1)):
        needchk = 1
    else :
        needchk = 0

    return needchk



# create  array 
def add_2d_element(arr, key1, key2, val):
    #print "add_2d_element ", key1, " ",key2
    if key1 in arr:
        arr[key1].update({key2: val})
    else:
        arr.update({key1: {key2: val}})

    return arr

#create==1 means if key1 or key2 doesn't exist, create new keys of arr
#create==0 means if key1 or key2 doesn
def twod_element_inc1(arr, key1, key2, use_init=0):
    global dbg_en
    if (dbg_en == 2):
        print "USER-DEF init array debug use_init = ", use_init
    if key1 in arr:
        if key2 in arr[key1]:
            arr[key1][key2]  =  arr[key1][key2] + 1
        elif (use_init == 0):
            add_2d_element(arr, key1, key2, 0) 
            arr[key1][key2]  =  arr[key1][key2] + 1
    elif (use_init == 0):
         add_2d_element(arr, key1, key2, 0) 

    return arr

def in_init_array(arr, key1, key2):
    #print "in_init_array check key1:", key1,"key2:",key2
    if key1 in arr:
        if key2 in arr[key1]:
            return 1
        else:
            return 0
    else:
        return 0


def init_array_from_file(f):
    CheckArr = {}
    keys = []
    with open(f, 'r') as f_r :
        lines= f_r.readlines()

    for i in range (0,len(lines)):
         key = lines[i].strip()
         matchObj=re.search(r'^##',key)
         if matchObj:
             print "Comment line found :", key
         else:
             keys.append(key)

    for i in range (0, len(keys)):
        for j in range(0, len(keys)):
            add_2d_element(CheckArr, keys[i], keys[j], 0)

    f_r.close()

    return CheckArr

def create_init_array(AllLogTransObjs, prefix=""):
    global dbg_en

    CheckArr = {}
    TransDef = []
    print len(AllLogTransObjs)
    if (dbg_en == 1):
        print "create init array "
    for i in range (0, len(AllLogTransObjs)):
        transdef = TransType.get_key(AllLogTransObjs[i])
        if (dbg_en == 1):
            print "init array for trans:", transdef
        if not(transdef in TransDef):
            TransDef.append(transdef)
            if (dbg_en == 1):
                print "Debug: append trans def", transdef
    print "TransDef = "
    print TransDef
    for i in range (0, len(TransDef)):
        for j in range(0, len(TransDef)):
            add_2d_element(CheckArr, TransDef[i], TransDef[j], 0)
    print "create init array CheckArr = "
    print CheckArr
    if (dbg_en == 1):
        f_init_arr = prefix + "." + "init_array.csv"
        CsvH.log_2dto_csv(CheckArr, f_init_arr)
    return CheckArr

def create_init_array_with_typef(AllLogTransObjs, type_f):
    global dbg_en

    CheckArr = {}
    TransDef = []
    keys = []


    with open(type_f, 'r') as f_r :
        lines= f_r.readlines()

    for i in range (0,len(lines)):
       key = lines[i].strip()
       if (dbg_en == 1):
           print "Check key from file :", key
       matchObj=re.search(r'^##',key)
       if matchObj:
           if (dbg_en == 1):
                print "Comment line found :", key
       else:
           keys.append(key)
           if (dbg_en == 1):
                print "Add key from file :", key

    for i in range (0, len(AllLogTransObjs)):
        transdef = AllLogTransObjs[i].PortName+"-"+AllLogTransObjs[i].L3Type
        if (dbg_en==3):
            if(AllLogTransObjs[i].L3Type!="NA"):
                print "find: ",AllLogTransObjs[i].PortName+"-"+AllLogTransObjs[i].L3Type
        if (dbg_en == 1):
            print "init array for trans:", transdef
        if not(transdef in TransDef):
            TransDef.append(transdef)
            if (dbg_en == 1):
                print "Debug: append trans def", transdef

    for i in range (0, len(keys)):
        for j in range(0, len(TransDef)):
            add_2d_element(CheckArr, keys[i], TransDef[j], 0)

    if (dbg_en == 1):
        f_init_arr = prefix + "." + "init_array.csv"
        CsvH.log_2dto_csv_a(CheckArr, f_init_arr)

    return CheckArr


#key1 typsube
def get_key_type(key):
    keys = key.split("-")
    if (len(keyinfo) == 1): #PortName
        return "Port"
    elif (len(keyinfo) == 2): #PortName-type
        return "Port-Type"
    else:
        return "UnDefined"

def check_based_on_cycles(AllLogTransObjs, CheckArr, prefix, use_init_array):
    global dbg_en

    SingalTransArr={} #arr which contains each trans hit times

    if (dbg_en == 1):
        #print "DEBUG-- check based on cycles -- ,check with cycles num:", crossCycles
        #f_dbg_name = prefix+"."+"cc_cycle.dbg"
        f_dbg_name = "cc_cycle.dbg"
        f_dbg = open(f_dbg_name, 'w')



    for i in range (0, len(AllLogTransObjs)):
        if (dbg_en == 2):
            print "DEBUG-- check based on cycles -- AllLogTransObjs-- ", AllLogTransObjs[i].PortName
        if (need_check(AllLogTransObjs[i])):
            start_check_cycle = AllLogTransObjs[i].ClkCycles
            start_check_line = i
            if (dbg_en == 1):
                f_dbg.write("Cross coverage check start : time window is ")
                f_dbg.write(str(crossCycles))
                f_dbg.write("\nCheck from line")
                f_dbg.write(str(start_check_line))
                f_dbg.write("   ")
                f_dbg.write(str(start_check_cycle))
                f_dbg.write("    ")
                f_dbg.write(AllLogTransObjs[i].PortName)
                f_dbg.write("\n")
                
            #TimeCheckArr.apped(AllLogTransObjs[i])

            key_of_singal_arr = TransType.get_key(AllLogTransObjs[start_check_line],CheckArr)
            if (dbg_en == 2):
                print "DEBUG-- singal csv -- ", key_of_singal_arr

            if key_of_singal_arr in SingalTransArr:
                SingalTransArr[key_of_singal_arr] = SingalTransArr[key_of_singal_arr] + 1
                if (dbg_en == 2):
                    print "DEBUG-- singal csv -- ", key_of_singal_arr, SingalTransArr[key_of_singal_arr] 
            else:
                SingalTransArr.update({key_of_singal_arr:1})
                if (dbg_en == 2):
                    print "DEBUG-- singal csv a-- ", key_of_singal_arr, SingalTransArr[key_of_singal_arr] 

            level_sig = TransType.is_level_sig(AllLogTransObjs[start_check_line])
            level_sig_start = TransType.is_level_sig_asrt(AllLogTransObjs[start_check_line])
            if (dbg_en == 2):
                print "DEBUG-- levelsig PortName- ", AllLogTransObjs[start_check_line].PortName 
                print "DEBUG-- levelsig sig- ", level_sig 
                print "DEBUG-- levelsig sig_start- ", level_sig_start 
            
            #if (TransType.is_level_sig_deasrt(AllLogTransObjs[start_check_line])==1):
            #    print "DEBUG-- levelsig sig_deasrt- don't log deasrt "
            #    break

            if (level_sig and level_sig_start):
                #f_dbg.write("check level sig start\n")
                for j in range (start_check_line+1, len(AllLogTransObjs)):
                    #f_dbg.write(str(j))
                    #f_dbg.write("   ")
                    #f_dbg.write(str(TransType.is_level_sig_deasrt(AllLogTransObjs[j])))
                    #f_dbg.write("\n")
                    if (TransType.is_level_sig_deasrt(AllLogTransObjs[j])==0):
                        trans1 = TransType.get_key(AllLogTransObjs[start_check_line], CheckArr)
                        trans2 = TransType.get_key(AllLogTransObjs[j], CheckArr)
                        inArr = in_init_array(CheckArr, trans1, trans2)
                        if ( j > start_check_line +1):
                            trans_tmp = TransType.get_key(AllLogTransObjs[j-1], CheckArr)

                            if (trans_tmp != trans2):
                                #f_dbg.write("Cross coverage Found \n")
                                #f_dbg.write(trans1)
                                #f_dbg.write("   ")
                                #f_dbg.write(trans2)
                                #f_dbg.write("\n")
                                twod_element_inc1(CheckArr,trans1, trans2, use_init_array)
                    else :
                        #f_dbg.write("check level sig end\n")
                        break

            else:
                for j in range (start_check_line+1, len(AllLogTransObjs)):
                    if (TransType.is_level_sig(AllLogTransObjs[j])):
                        #f_dbg.write("skip level sig if it isn't asserted\n")
                        break
                    inCycleWindow = TransType.cross_based_on_cycles(AllLogTransObjs[start_check_line],AllLogTransObjs[j], crossCycles)
                    cyclenum = int(TransType.cycle_window(AllLogTransObjs[start_check_line],AllLogTransObjs[j]))
                    trans1 = TransType.get_key(AllLogTransObjs[start_check_line], CheckArr)
                    trans2 = TransType.get_key(AllLogTransObjs[j], CheckArr)
                    #print "DEBUG-- to check whether transtype is in init_array trans1 -- ",  trans1, "trans2 -- ", trans2
                    inArr = in_init_array(CheckArr, trans1, trans2)
                    #print "DEBUG-- inCycleWindow is -- ",  inCycleWindow, "cycle num is --", cyclenum
                    #print "DEBUG-- inArr is -- ",  inArr
                    if (int(inCycleWindow) == 0):
                        break

                    if (need_check(AllLogTransObjs[j]) and ((use_init_array==0) or (inArr==1))) :
                        if (dbg_en == 1):
                            f_dbg.write("Cross coverage Found \n")
                            f_dbg.write("Debug :  start_check_cycle=")
                            f_dbg.write(str(start_check_cycle))
                            f_dbg.write(" ***  current cycle=")
                            f_dbg.write(str(AllLogTransObjs[j].ClkCycles))
                            f_dbg.write(" *** gap is ")
                            f_dbg.write(str(AllLogTransObjs[j].ClkCycles - start_check_cycle))
                            f_dbg.write("\n")
                            f_dbg.write(trans1)
                            f_dbg.write("   ")
                            f_dbg.write(trans2)
                            f_dbg.write("   ")

                        if ( j > start_check_line +1):
                            trans_tmp = TransType.get_key(AllLogTransObjs[j-1], CheckArr)

                            if (trans_tmp != trans2):
                                twod_element_inc1(CheckArr,trans1, trans2, use_init_array)
                                if (dbg_en == 1):
                                    f_dbg.write("different with prevoius trans type, add 1 --- \n")
                                    f_dbg.write(str(CheckArr[trans1][trans2]))
                                    f_dbg.write("CheckArr[{}][{}]={}".format(trans1, trans2, CheckArr[trans1][trans2]))
                            else:
                                if (dbg_en == 1):
                                    f_dbg.write("same with prevoius trans type, skip --- ")
                        else:
                            if (dbg_en == 1):
                                print "DEBUG-- don't needcheck", trans1,"---",trans2
                        

                    else:
                        break

                    
    if (dbg_en == 1):
        f_dbg.close()

    #if (dbg_en == 1):
    if(dbg_en == 3):
        fname_1d = prefix+"."+"single_trans.csv"
        CsvH.log_1dto_csv(SingalTransArr, fname_1d)
        fname_2d = prefix+"."+"cc_cycle.csv"
        CsvH.log_2dto_csv(CheckArr, fname_2d)

    return CheckArr
 




#TODO: this function need to be re-wriiten : 2022-9-15
def check_based_on_time(AllLogTransObjs, CheckArr):
    #global TimeCheckArr
    start_check_time = 0
    start_check_line = 0

    f_w = open("cc_time.csv", 'w')
    
    for i in range (0, len(AllLogTransObjs)):
        start_check_time = AllLogTransObjs[i].FinishTimestamp
        start_check_line = i
        f_w.write("Cross coverage check start : time window is ")
        f_w.write(str(crossTime))
        f_w.write("\nCheck from line")
        f_w.write(str(start_check_line))
        f_w.write("   ")
        f_w.write(str(start_check_time))
        f_w.write("    ")
        f_w.write(AllLogTransObjs[i].PortName)
        f_w.write("\n")
        #f_w.write("cross coverage check from line ", start_check_line)
        #f_w.write("cross coverage check from time ", start_check_time)
            
        #TimeCheckArr.apped(AllLogTransObjs[i])

        f_w.write("Debug :  start_check_time=")
        f_w.write(str(start_check_time))
        f_w.write(" ***  current timestamp=")
        f_w.write(str(AllLogTransObjs[i].FinishTimestamp))
        f_w.write(" *** gap is ")
        f_w.write(str(AllLogTransObjs[i].FinishTimestamp - start_check_time))
        f_w.write("\n")

        if ((AllLogTransObjs[i].FinishTimestamp - start_check_time < crossTime) and (i>start_check_line)):
            f_w.write("Cross coverage Found \n")
            f_w.write(str(start_check_line))
            f_w.write("   ")
            f_w.write(AllLogTransObjs[start_check_line].PortName)
            f_w.write(" ***  ")
            f_w.write(str(i))
            f_w.write("   ")
            f_w.write(AllLogTransObjs[i].PortName)
            f_w.write("\n")
            #f_w.write("cross ",AllLogTransObjs[i].PortName,"---",AllLogTransObjs[i].Timestamp )
        elif ((start_check_line != len(AllLogTransObjs) -1) and (start_check_line != i)):
            start_check_line = start_check_line + 1
            start_check_time = AllLogTransObjs[start_check_line].FinishTimestamp
            f_w.write("Cross coverage check for line")
            f_w.write(str(start_check_line))
            f_w.write("    ")
            f_w.write(str(start_check_time))
            f_w.write("    ")
            f_w.write(AllLogTransObjs[i].PortName)
            f_w.write("\n")
            #f_w.write("cross coverage check from line ", start_check_line)
            #f_w.write("cross coverage check from time ", start_check_time)

    f_w.close()
    
   

def save_trans_to_file(filename, AllLogTransObjs):

    with open(filename, 'w') as f_w :
        for i in range (0,len(AllLogTransObjs)):
            f_w.write(AllLogTransObjs[i].PortName)
            f_w.write("    ")
            f_w.write(str(AllLogTransObjs[i].FinishTimestamp))
            f_w.write("\n")
        



def generate_cc_cycle(f="",prefix=""):
    global dbg_en
    #print("In-generate_cc_cycle for file %s, prefix=%s" %(f,prefix))

    parse_para()
    if (f == ""):
        f=chk_file

    prefix = "nbifss"       #DEBUG

    AllLogTransObjs=[]
    CheckArr  = {}
    fnames = os.path.split(f)
    path = fnames[0]

    os.chdir(path)
    intffile = fnames[1]


    #clkfile = prefix+"."+"clock_info.log"
    csvfile = prefix+"."+"cc_cycle.csv"
    #userdef_file = prefix+"."+"rtl_user_def_info.log"
    #clkfile = prefix+"clock_info.log"
    #csvfile = prefix+"cc_cycle.csv"
    clkfile = "clock_info.log"
    userdef_file = "user_def_info.log"
    #userdef_file = prefix+"rtl_user_def_info.log"

    if(dbg_en == 1):
        print "DEBUG-- work directory is ", path
        print "DEBUG-- get clockinfo from file ", clkfile
        print "DEBUG-- get user def info from file", userdef_file
        print "DEBUG-- get intfinfo from file ", f

    ClkInfoArr = get_clkinfo_from_file(clkfile)
    userdef_path = path+"//"+userdef_file
    print(userdef_path)
    if(os.path.exists(userdef_path)):
        print "userdef path exists:"+userdef_path
        UserDefInfoArr = get_user_def_info_from_file(userdef_file)
    else:
        print "userdef path not exist"
        UserDefInfoArr = []
    print os.getcwd()
    print intffile
    AllLogTransObjs  = read_trans_from_file(intffile, ClkInfoArr, UserDefInfoArr)
    #print "00 init array for trans:", AllLogTransObjs

    if(dbg_en == 1):
        f_translog = prefix+"."+"trans.log"
        save_trans_to_file(f_translog, AllLogTransObjs)

    if (type_f==""):
        if (dbg_en == 1):
            print "No trans type is specified, generate all trans types in log file"
        #print "aa init array for trans:", AllLogTransObjs
        use_init_array = 0
        CheckArr = create_init_array(AllLogTransObjs) #create init_array_based_on transtype in AllLogTransObjs
    else:
        if (dbg_en == 1):
            print "trans type is specified in file,", type_f
        use_init_array = 1
        if (cross_with_all_types == 1) :
            CheckArr = create_init_array_with_typef(AllLogTransObjs, type_f)
            print("DEBUG:create init array with typef")
        else:
            CheckArr  = init_array_from_file(type_f) #init array need to get from some cfg file
    print "CheckArr lists below"
    print CheckArr
    if (based_on_cycle==1):
        CheckArr = check_based_on_cycles(AllLogTransObjs, CheckArr, prefix, use_init_array)
    else:
        check_based_on_time(AllLogTransObjs, CheckArr, use_init_array) #this function isn't maitained

    trans_dbg.close()
    
    return CheckArr

def parse_para():
    if len(sys.argv) < 3 :
       print "Error: at least need 3 args!" 
       print "usuage:"
       print "must needed args:"
       print "      -f <intflog name>: such as : intf_CLIENT_SHUB.nbif_dcgfx.log  "
        
       sys.exit(1)
   

    for i in range (1, len(sys.argv)):
#cc_cov.py only --start -f to assign the input signal file
        if sys.argv[i] == "-f" :
            global chk_file
            chk_file = sys.argv[i+1]
            i=i+1
#cc_cov.py only --end -f to assign the input signal file

        if sys.argv[i]=="-tt": #specify the trans types which need to be cross-checked
            global type_f
            type_f =sys.argv[i+1]
            i=i+1

        if sys.argv[i]=="-cc_with_all_types": #specify the trans types which need to be cross-checked
            global cross_with_all_types
            cross_with_all_types=int(sys.argv[i+1])
            i=i+1

        if sys.argv[i]=="-cycles":
            global crossCycles
            crossCycles=int(sys.argv[i+1])
            i=i+1

        if sys.argv[i]=="-collect_output":
            global collect_output
            collect_output=int(sys.argv[i+1])
            i=i+1

        if sys.argv[i]=="-collect_input":
            global collect_input
            collect_input=int(sys.argv[i+1])
            i=i+1

        if sys.argv[i]=="-collect_cmpl":
            global collect_cmpl
            collect_cmpl=int(sys.argv[i+1])
            i=i+1

        if sys.argv[i]=="-check_output":
            global check_output
            check_output=int(sys.argv[i+1])
            i=i+1

        if sys.argv[i]=="-check_input":
            global check_input
            check_input=int(sys.argv[i+1])
            i=i+1

        if sys.argv[i]=="-check_cmpl":
            global check_cmpl
            check_cmpl=int(sys.argv[i+1])
            i=i+1

        if sys.argv[i]=="-based_on_cycle":
            global based_on_cycle
            based_on_cycle=int(sys.argv[i+1])
            i=i+1

        if sys.argv[i]=="-dbg_en":
            global dbg_en
            dbg_en=int(sys.argv[i+1])
            i=i+1

    #print "ARGS: -dbg_en=", dbg_en
    #print "ARGS: -based_on_cycle=", based_on_cycle
    #print "ARGS: -collect_input=", collect_input 
    #print "ARGS: -collect_output=", collect_output
    #print "ARGS: -check_input=", check_input 
    #print "ARGS: -check_output=", check_output

def main():



#        f = "/proj/cip_nbif_regression_2/ecwang/nbif/ws_sanity/out/linux_3.10.0_64.VCS/nbif_draco_gpu/config/nbif_all_rtl/run/nbif-draco_gpu-rembrandt/nbiftdl/demo_test_host_nbif_all_rtl/intf_CLIENT_SHUB.nbif_dcgfx.log"

    generate_cc_cycle()




if __name__=='__main__':
  main()

