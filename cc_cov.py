#!/tool/pandora64/bin/python3.10

#demo command:  python cross_cov.py -i intf_CLIENT_SHUB.nbif_chtgfx.log -clk clock_info.log -o save.log

#this script is used to generate coverage for one test
#input is intf*log and clock_info.log
#output is csv file (option)
#output is 2d array by default

import os,sys
import subprocess
import re
import json

#use-defined module
import get_trans_type as TransType
import csv_handle as CsvH

#global define
#type_f = "/proj/cip_nbif_dv_misc_1/danliu22/nbif/ws_1/python/cross_coverage/2.0/nbif/need_chk_trans_type_test.txt"
chk_file  = ""
based_on_cycle=1 # check cross coverage based on cycle nubmers or based on realtime
type_f = ""
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
type_file_keys = []
trans_dbg = open(trans_dbg_name,'w')

#temp array for cross coverage check same clock domain based on cycles.
#per clock

crossCycles = 20
#"Trans1""Trans2"  HDP_WR HDP_FLUSH CPF_WR
#"HDP_FLUSH" may be reported as "HDP_RD"
#HDP_FLUSH == HDP_RD && DATA=0
#
#
crossTime = 20000
class LogTrans:
    'class for a trans in intf.log'


    def __init__(self, RawTxt, clkarr, userarr, userbitarr):
        #basic name info
        self.RawTxt=RawTxt
        self.ClkInfoArr=clkarr
        self.UserDefInfoArr=userarr
        
        self.PortName = ""
        self.ClkName = "LCLK"
        self.StartTimestamp = ""
        self.Timestamp = int(0)
        self.Direction = ""
        self.PortID = ""
        self.Type = ""
        self.ReqBUsNum = ""
        self.ReqID = ""
        self.VF = ""
        self.VFID = ""
        self.AxiID = ""
        self.TagID = ""
        self.CpldID = ""
        self.Chain = ""
        self.AddrH = ""
        self.AddrL = ""
        self.AddrAlign = ""
        self.CMD = ""
        self.BE = ""
        self.Index = ""
        self.DataFinishTime = ""
        self.DataBusNum = ""
        self.Data4 = ""
        self.Data3 = ""
        self.Data2 = ""
        self.Data1 = ""
        self.DataAlign = ""
        self.EP = ""
        self.UserBit = ""
        self.ClkPeriod = float(0)
        self.CLkCycles = 0
        self.Data=""
        self.UserDefType = "NA"

        self.GetTransInfo()
        self.GetTypeFromUserBit(userbitarr)

    def GetTransInfo(self):
        
        port_len = 15 #before is 11, some port like ACP_DOORBELL is longer
        clk_len = 10
        start_time_len = 11
        finish_time_len = 11
        dir_len = 2
        #portid_len = 2
        portid_len = 3
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
        if total_len<210:
            return
        userbit_len = total_len-172
        start_len = 0
        end_len = port_len
        self.PortName=self.RawTxt[start_len : end_len].strip() #[0:11]
        start_len = end_len
        end_len  = end_len + clk_len
        self.ClkName=self.RawTxt[start_len : end_len].strip() #[11:22]
        start_len = end_len
        end_len  = end_len + start_time_len
        self.StartTimestamp=self.RawTxt[start_len : end_len].strip() #[22:33]
        #print self.ClkName
        start_len = end_len
        end_len  = end_len + finish_time_len
        timestamp_str = self.RawTxt[start_len : end_len].strip()
        if (timestamp_str.isdigit()):
            self.Timestamp=int(self.RawTxt[start_len : end_len].strip()) #[22:33]
        else:
            self.Timestamp=int(00000000)
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
        start_len = end_len 
        end_len  = total_len
        self.UserBit =  self.RawTxt[start_len : end_len].strip() #[89:98]

        self.ClkPeriod = float(self.ClkInfoArr[self.ClkName]) * 1000
        #print self.ClkPeriod
        #print self.Timestamp
        self.ClkCycles = int(self.Timestamp // self.ClkPeriod)
        self.Data=""
        self.UserDefType = "NA"
        #self.L1Type=NP/P
        #self.L2Type=MEM_RD ATOMICE MEW_WR
        #self.L3Type=FLUSH FETCH_ADD MEM_WR
        #if (lineinfo[14] != "--------"):
        for n in range(len(self.UserDefInfoArr)):
            if((str(self.Timestamp) == str(self.UserDefInfoArr[n][0])) and (str(self.AxiID) == str(self.UserDefInfoArr[n][1]))):
                self.UserDefType = self.UserDefInfoArr[n][2]      #get user_def_type in terms of realtime and unit_id or axi_id
                break
        self.L1Type = TransType.get_transtype(self, "L1Type")
        self.L2Type = TransType.get_transtype(self, "L2Type")
        self.L3Type = TransType.get_transtype(self, "L3Type")
        if(dbg_en==3):
            if(self.L3Type!="USER_NA"):
                print self.Timestamp,self.L3Type

    def GetTypeFromUserBit(self,userbitarr):
    #trans_type_list,port_list,bit_type_list,field_list,value_match_list
        trans_type_list = userbitarr[0]
        port_list = userbitarr[1]
        #bit_type_list = userbitarr[2]
        #field_list = userbitarr[3]
        value_match_list = userbitarr[4]
        user_bit = self.UserBit.replace(" ","")
        #UserBitBinary = bin(int(user_bit,16))
        if re.search("x",user_bit)==None and re.search("-",user_bit)==None and len(user_bit)!=0 and re.search("[A-Z]",user_bit)==None:
            #print(user_bit)
            user_bit = bin(int(user_bit,16))
        else:
            return
        for n in range(len(value_match_list)):
            if self.PortName == port_list[n] and re.search(value_match_list[n],user_bit)!=None:
                self.UserDefType = trans_type_list[n]
                self.L1Type = TransType.get_transtype(self, "L1Type")
                self.L2Type = TransType.get_transtype(self, "L2Type")
                self.L3Type = TransType.get_transtype(self, "L3Type")

                trans_dbg.write("----------------------\n")
                trans_dbg.write(self.UserBit+"\n")
                trans_dbg.write(user_bit+"\n")
                trans_dbg.write(self.UserDefType+"\n")
                trans_dbg.write("----------------------\n")
                #trans_dbg.write(user_bit+"\n")
                break

        #print user_bit
        
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

        #trans_dbg.write("Trans info:\n")
        #trans_dbg.write("    PortName : "+str(self.PortName)+"\n")
        #trans_dbg.write("    L3Type     : "+str(self.L3Type)+"\n")
        #trans_dbg.write("    UserDefType  : "+str(self.UserDefType)+"\n")
        trans_dbg.write(self.UserBit+"\n")

def get_clkinfo_from_file(filename):
    global dbg_en
    ClkInfoArr={}
    with open(filename, 'r') as f_r :
        clk_lines= f_r.readlines()

    for i in range (0,len(clk_lines)):
        clk_info = clk_lines[i].split()
        clk_name = clk_info[0]
        ClkInfoArr[clk_name] = clk_info[1]
    if (dbg_en == 0):
        print "Clock Info:", ClkInfoArr
    f_r.close()
    return ClkInfoArr
def get_field_info_from_file(intffile,jsonfilename):
    global dbg_en
    UserBitInfoArr = []
    trans_type_list = []
    port_list = []
    bit_type_list = []
    field_list = []
    value_list = []
    value_match_list = []

    with open(jsonfilename,'r') as f_r:
        UserBitInfoArr = json.load(f_r)
    variant_name = UserBitInfoArr.keys()
    for variant in variant_name:
        if re.search(variant,intffile)!=None:
            break
    for trans_type in UserBitInfoArr[variant].keys():
        port_key_list = UserBitInfoArr[variant][trans_type].keys()
        for port_key in port_key_list:
            port_line = port_key.split(",")
            for port in port_line:
                trans_type_list.append(trans_type)
                port_list.append(port)
                bit_type_list.append(UserBitInfoArr[variant][trans_type][port_key]["BitType"])
                field_list.append(UserBitInfoArr[variant][trans_type][port_key]["Field"])
                value_list.append(UserBitInfoArr[variant][trans_type][port_key]["Value"])
    for n in range(len(field_list)):
        field_split = field_list[n].split(":")
        width = int(field_split[0])-int(field_split[1])+1
        value_binary = str(bin(int(value_list[n])))
        value_binary = value_binary.replace("0b","")
        value_binary = value_binary.rjust(width,'0')
        if field_split[1]!=0:
            for n in range(int(field_split[1])):
                value_binary  += "."
        value_binary  = ".*"+value_binary
        value_match_list.append(value_binary)

    return trans_type_list,port_list,bit_type_list,field_list,value_match_list
    
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


def read_trans_from_file(filename, clkarr, userarr, userbitarr):
    global dbg_en
    global type_file_keys
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
            matchObj=re.search(r'^---------',saved_log_lines[i])
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
                        iTrans=LogTrans(saved_log_lines[i], clkarr, userarr, userbitarr)
                        if (need_log(iTrans)):
                            AllLogTransObjs.append(iTrans)
                #else:
                    #AllLogTransObjs[len(AllLogTransObjs)-1].AddDataLine(saved_log_lines[i]) #add this data line to last trans

    if(dbg_en == 5):
        for item in AllLogTransObjs:
            print item.PortName+"-"+item.L3Type
    if (dbg_en == 2):
        for i in range (0,len(AllLogTransObjs)):
            AllLogTransObjs[i].TransPrint()       

    f_r.close()
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
    #global type_file_keys
    needchk = 0
    #if (cross_with_all_types):
        #match_str = logtrans.PortName+"-"+logtrans.L3Type
        #for _type in type_file_keys:
            #if (re.match(match_str,_type)!=None):
                #needchk = 1
                #if(dbg_en == 5):
                    #print _type+" need check"
                #return needchk
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
    needchk = 1
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
def twod_element_inc1(arr, key1, key2, use_init=0):     #cross num + 1
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
    if len(prefix)==0:
        prefix = "nbif"
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

    for i in range (0, len(TransDef)):
        for j in range(0, len(TransDef)):
            add_2d_element(CheckArr, TransDef[i], TransDef[j], 0)
    if (dbg_en == 2):
        f_init_arr = prefix + "." + "init_array.csv"
        CsvH.log_2dto_csv(CheckArr, f_init_arr)
    return CheckArr

def create_init_array_with_typef(AllLogTransObjs,type_f):
    global dbg_en

    CheckArr = {}
    TransDef = []
    keys = []
    check_trans = []
    
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
        transdef = TransType.get_key(AllLogTransObjs[i])
        TransDef.append(transdef)
    for trans in TransDef:
        for key in keys:
            if key in trans:
                #print "match key : ",key
                check_trans.append(trans)
                break
    for i in range (0, len(check_trans)):
        for j in range(0, len(check_trans)):
            add_2d_element(CheckArr, check_trans[i], check_trans[j], 0)

    #prefix = "nbif"
    #if (dbg_en == 1):
        #f_init_arr = prefix + "." + "init_array.csv"
        #CsvH.log_2dto_csv_a(CheckArr, f_init_arr)

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

def check_based_on_cycles(AllLogTransObjs, CheckArr, prefix, use_init_array, cross_with_total_types):
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
    if (dbg_en == 1):
        if (cross_with_total_types == 1):
            #fname_1d = prefix+"."+"total_single_trans.csv"
            #CsvH.log_1dto_csv(SingalTransArr, fname_1d)
            fname_2d = prefix+"."+"total_cc_cycle.csv"
            CsvH.log_2dto_csv(CheckArr, fname_2d)
        else:
            #fname_1d = prefix+"."+"filtered_single_trans.csv"
            #CsvH.log_1dto_csv(SingalTransArr, fname_1d)
            fname_2d = prefix+"."+"filtered_cc_cycle.csv"
            CsvH.log_2dto_csv(CheckArr, fname_2d)
    if (dbg_en == 2):
        if (cross_with_total_types == 1):
            fname_1d = prefix+"."+"total_single_trans.csv"
            CsvH.log_1dto_csv(SingalTransArr, fname_1d)
        else:
            fname_1d = prefix+"."+"filtered_single_trans.csv"
            CsvH.log_1dto_csv(SingalTransArr, fname_1d)

    return CheckArr




#TODO: this function need to be re-wriiten : 2022-9-15
def check_based_on_time(AllLogTransObjs, CheckArr):
    #global TimeCheckArr
    start_check_time = 0
    start_check_line = 0

    f_w = open("cc_time.csv", 'w')
    
    for i in range (0, len(AllLogTransObjs)):
        start_check_time = AllLogTransObjs[i].Timestamp
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
        f_w.write(str(AllLogTransObjs[i].Timestamp))
        f_w.write(" *** gap is ")
        f_w.write(str(AllLogTransObjs[i].Timestamp - start_check_time))
        f_w.write("\n")

        if ((AllLogTransObjs[i].Timestamp - start_check_time < crossTime) and (i>start_check_line)):
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
            start_check_time = AllLogTransObjs[start_check_line].Timestamp
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
            f_w.write(str(AllLogTransObjs[i].Timestamp))
            f_w.write("\n")
        



def generate_cc_cycle(f="",prefix=""):
    global dbg_en
    global type_file_keys
    if len(prefix) == 0:
        prefix = "nbif"
    #print("In-generate_cc_cycle for file %s, prefix=%s" %(f,prefix))

    parse_para()
    if (f == ""):
        f=chk_file

    

    AllLogTransObjs=[]
    CheckArrTotal  = {}
    CheckArrFilter = {}
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
    json_file = "/proj/cip_nbif_dv_misc_1/danliu22/nbif/ws_1/python/cross_coverage/2.0/nbif/user_define_trans_type.json"
    if(dbg_en == 1):
        print "DEBUG-- work directory is ", path
        print "DEBUG-- get clockinfo from file ", clkfile
        print "DEBUG-- get user def info from file", userdef_file
        print "DEBUG-- get intfinfo from file ", f

    ClkInfoArr = get_clkinfo_from_file(clkfile)
    UserBitInfoArr = get_field_info_from_file(intffile,json_file)
    #print UserBitInfoArr
    userdef_path = path+"/"+userdef_file
    if(os.path.exists(userdef_path)):
        print "userdef path exists:"+userdef_path
        UserDefInfoArr = get_user_def_info_from_file(userdef_file)
    else:
        print "userdef path not exist"
        UserDefInfoArr = []
    AllLogTransObjs  = read_trans_from_file(intffile, ClkInfoArr, UserDefInfoArr, UserBitInfoArr)
    #print "00 init array for trans:", AllLogTransObjs
    CheckArr = create_init_array(AllLogTransObjs) #create init_array_based_on transtype in AllLogTransObjs
    use_init_array = 0
    if (based_on_cycle==1):
        CheckArrTotal = check_based_on_cycles(AllLogTransObjs, CheckArr, prefix, use_init_array, 1)
    else:
        check_based_on_time(AllLogTransObjs, CheckArr, use_init_array) #this function isn't maitained
    if(dbg_en == 2):
        f_translog = prefix+"."+"trans.log"
        save_trans_to_file(f_translog, AllLogTransObjs)
    if (type_f != "") :
        #CheckArr = create_init_array_with_typef(AllLogTransObjs,type_f)
        use_init_array = 1
        if (cross_with_all_types):
            CheckArr  = create_init_array_with_typef(AllLogTransObjs,type_f) #init array need to get from some cfg file
            print("DEBUG:create init array with typef")
        else:
            CheckArr  = init_array_from_file(type_f) #init array need to get from some cfg file
        if (based_on_cycle==1):
            CheckArrFilter = check_based_on_cycles(AllLogTransObjs, CheckArr, prefix, use_init_array, 0) 
        else:
            check_based_on_time(AllLogTransObjs, CheckArr, use_init_array) #this function isn't maitained

    #create_init_array_with_typeftrans_dbg.close()
    
    return CheckArrTotal,CheckArrFilter

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

