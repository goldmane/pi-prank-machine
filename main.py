import serial;
import time;
import sys;
from subprocess import call;
from colorama import Fore, Back, Style;

CMD_AT = "AT\r";

ERRMSG_SERIAL_CHECK = "Is USB connected?";
ERRMSG_STARTUP_CHECK = "Failed startup check. There should be a more detailed message.";

ser = None;

def passFail(b, msg, exitOnFail=False, exitMessage=""):
    print(msg + ": "),
    print(Fore.GREEN + "PASS" if b else Fore.RED + "FAIL"),
    print(Fore.RESET);
    if exitOnFail and not b:
        raise Exception(ERRMSG_SERIAL_CHECK);
        exit(-1);
    return b;

def initializeSerial():
    try:
        global ser;
        ser  = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1);
        return True;
    except: 
        return False;

def cleanup():
    ser.close();

def writeCommand(cmd):
    global ser;
    if ser.inWaiting() > 0:
        ser.flushInput();
    ser.write(cmd.encode());
    res = ser.read(100);
    ser.flush();
    return res;

def cmdAT():
    res = writeCommand(CMD_AT);
    lines = res.splitlines();
    if len(lines) == 3 and lines[0] == "AT" and lines[2] == "OK":
        return True;
    else: 
        return False;

def checkBattery():
    res = writeCommand("AT+CBC\r");
    lines = res.splitlines();
    if lines[0] == "AT+CBC":
        print "Battery %: ",
        print Fore.YELLOW + lines[2].replace("+CBC: ","").split(",")[1] + Fore.RESET;
    else:
        raise Exception("Issue reading battery info");

def checkSMS():
    res = writeCommand("AT+CPMS=\"SM\"\r");
    lines = res.splitlines();
    if lines[0] == "AT+CPMS=\"SM\"" and lines[4] == "OK":
        return int(lines[2].replace("+CPMS: ","").split(",")[0]);
    else:
        return 0;

def readSMS(i):
    res = writeCommand("AT+CMGR="+str(i)+"\r");
    lines = res.splitlines();
    if lines[0] == "AT+CMGR="+str(i) and lines[5] == "OK":
        return lines[3];
    else:
        raise Exception("Error reading text");

def deleteSMS(i):
    res = writeCommand("AT+CMGD="+str(i)+"\r");
    lines = res.splitlines();
    if lines[0] == "AT+CMGD="+str(i) and lines[2] == "OK":
        return True;
    else:
        raise Exception("Could not delete SMS #" + str(i));

def startupCheck():
    passFail(cmdAT(), "FONA Test", True, "Error sending AT command");
    res = writeCommand("AT+CMGF=1\r");
    lines = res.splitlines();
    passFail((lines[0] == "AT+CMGF=1" and lines[2] == "OK"), "CMGF", True, "Error running AT+CMGF=1");
    return True;

if __name__ == '__main__':
    try:
        passFail(initializeSerial(), "Initialize Serial", True, ERRMSG_SERIAL_CHECK);
        passFail(startupCheck(), "Startup Check", True, ERRMSG_STARTUP_CHECK);

        #This is the main loop
        loopOK = True;
        while loopOK:
            checkBattery();
            numSMS = checkSMS();
            if numSMS > 0:
                for i in xrange(numSMS):
                    smsText = readSMS(i+1);
                    tts = call("echo " + smsText + " | festival --tts", shell=True);
                    deleteSMS(i+1);
                    time.sleep(3);
            time.sleep(5); 
    except:
        cleanup();
        raise;
