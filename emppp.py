# -*- coding: utf8 -*-
from threading import Thread
from socket import *
from time import ctime
import time
import hashlib
import Queue 
import struct
import MySQLdb
import math
import urllib
import re
import ConfigParser
import os

SequenceID = 0
#回调地址队列，防止建立太多的socket

backUrlList = Queue.Queue(maxsize = 0)
#发信队列
sendMsgList = Queue.Queue(maxsize = 0)

#消息队列，缓存在这，防止被卡死溢出
recvMsgList = Queue.Queue(maxsize = 0)
class threadList:
    recv=None
    send=None
    test=None
    act=None
    cur=None
    br=None
    st=None
    pm=None
    
    
class app:
    latestActiveTime=None
    recvDataFlag = True
    sendDataFlag = True
    activeTestFlag = True
    isNotSubmit = True
    connectedTestFlag = True
    backTime = True
    tcp=None
    db = None
    br = True
    st = True
    pm = True
    isRestart = False
    wait = False
class dbPool:
    '''数据库连接池'''
    def __init__(self):
        
        self.minLength = 10
        self.maxLength = 30
        self.lNum = 0
        self.dbList = Queue.Queue(maxsize = self.maxLength)
        self.createL(self.minLength)
            
    def createL(self,num=1):
        G_var = Global_var()
        for i in range(0,num):
            self.lNum = self.lNum+1
            self.dbList.put(MySql(G_var,self.lNum))
    def getLink(self):
        
        if self.lNum<self.maxLength and self.dbList.empty():
            self.createL(1)
        return self.dbList.get()

    def pushBack(self,db):
        
        if self.lNum>self.minLength:
            self.destroyDb(db)
            self.lNum = self.lNum-1
        else:
            self.dbList.put(db)

    def destroyDb(self,db):
        try:
            db.cur.close()    #关闭指针
            db.db.close()
        except Exception,e:
            pass
class Global_var:
    '''全局变量'''
    def __init__(self):
        #加载配置文件
        self.configPath = 'config.ini'
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read(self.configPath)


        
        #端口相关
        self.host = self.cfg.get('empp','host')
        self.port = self.cfg.getint('empp','port')
        self.BuffSize = 1024
        self.addr = (self.host,self.port)

        #数据库相关
        self.host = self.cfg.get('mysql','host')
        self.db = self.cfg.get('mysql','db')
        self.user = self.cfg.get('mysql','user')
        self.charset = self.cfg.get('mysql','charset')
        self.passwd = self.cfg.get('mysql','passwd')
        self.mysqlPort = self.cfg.getint('mysql','port')
        
        #帐号相关
        self.ClientID = self.cfg.get('account','ClientID')
        self.AuthenticatorClient = self.cfg.get('account','AuthenticatorClient')
        self.serviceId = self.cfg.get('account','serviceId')
        #其他配置
        self.phone = self.cfg.get('other','phone')
        
            #初始值
        self.SequenceID = 0
    def GetTimeStamp(self):
        return int(time.strftime('%m%d%H%M%S'))
    def GetTimeStampString(self):
        return time.strftime('%m%d%H%M%S')
    def GetAuth(self):
        auth = self.ClientID+'\0\0\0\0\0\0\0\0\0'+self.AuthenticatorClient+self.GetTimeStampString()
        
        result = hashlib.new("md5",auth).digest()
        return result
class MySql:
    '''数据库类'''
    def __init__(self,G_var,no=10000):
        self.no = no
        try: 
            self.db = MySQLdb.connect(host=G_var.host,\
                                      db=G_var.db,user=G_var.user,\
                                      passwd=G_var.passwd,\
                                      charset=G_var.charset,\
                                      port=G_var.mysqlPort
                                      )
            self.cur = self.db.cursor()
        except Exception,e:
            
            writeLog("error:"+'db connect failed line 142'+e.__str__())
        return
    def query(self,sql):
        try:
            a = self.cur.execute(sql)
            
            return a
        except Exception,e:
            print e.__str__()
            G_var = Global_var()
            
            self.__init__(G_var,self.no)
            
            self.error_do(e.__str__(),sql)
            
            writeLog("search failed"+e.__str__()+sql)
            return False
    def error_do(self,msg,sql):
        if '2006' in msg or '2013' in msg:
            try:
                self.cur.execute(sql)
                
            except Exception,e:
                pass
    def GetOne(self,sql):
        self.query(sql)
        try:
            return self.cur.fetchall()[0]
            
        except Exception,e:
            return False
        
    def GetAll(self,sql):
        self.query(sql)
        try:
            return self.cur.fetchall()
        except Exception,e:
            return False
        
    def close(self):
        try:
            if self.db:
                self.cur.close()    #关闭指针
                self.db.close()
        except Exception,e:
            writeLog(e.__str__()+'1')

def checkPhone(phone):
    if re.match("^134|135|136|137|138|139|150|151|157|158|159|187|188|182",phone) is not None:
        return 1
    elif re.match("^130|131|132|155|156|185|186",phone) is not None:
        return 2
    else:
        return 3
    
def GetSequenceID():
    global SequenceID
    SequenceID = SequenceID+1
    if SequenceID>0xFFFFFFFF:
        SequenceID=0x00000000
    return SequenceID
class SMGP_head:
    '''保存头消息的东西'''
    def __init__(self):
        '''constructor'''
        self.PacketLength=0
        self.RequestID=0
        self.SequenceID=1
    def Length(self):
        return 42

class SMGP_login:
    '''登录'''
    def __init__(self,s):
        setStatus(u'login...')
        self.socket = s
        self.head = SMGP_head()
        self.head.PacketLength = 42
        self.head.RequestID = 1
        self.head.SequenceID=2
    def login(self):
        G_var = Global_var();
        loginCheck().start()
        try:
            #头
            self.socket.send(struct.pack('!I',54))
            self.socket.send(struct.pack('!I',1))

            self.socket.send(struct.pack('!I',GetSequenceID()))
            
            #体
            self.socket.send(struct.pack('!21s',G_var.ClientID))
            self.socket.send(G_var.GetAuth())
            
            
            self.socket.send(struct.pack('!B',0x10))
            
            self.socket.send(struct.pack('!I',G_var.GetTimeStamp()))
            
        except Exception,e:
            print 'login failed！'
            return
        
def addslashes(msg):
    msg = msg.replace("'","\\'");
    msg = msg.replace('"','\\"');
    return msg
#发信
class SMGP_submit:
    '''提交短信'''
    def __init__(self,s,phone,msg,db,poolID):
        self.socket = s
        self.db = db
        app.latestActiveTime = time.time()
        self.sendData(phone,msg,poolID)
        self.success = False
        
    def sendData(self,phone,msg,poolID):
        config = Global_var()
        app.isNotSubmit = False
        
        temp_msg = addslashes(msg)
        
        msg = msg.decode("utf-8")
        
        msg = msg.encode("GBK")
        
        
        
        length = len(msg);
        
        try:
            self.socket.send(struct.pack('!I',215+length))
            
            self.socket.send(struct.pack('!I',4))
            
            SeqID = GetSequenceID()
            self.socket.send(struct.pack('!I',SeqID))
        except Exception,e:
            restart().start()
            return False
            writeLog(e.__str__())

        
        #print "号码:"+phone+'内容:"'+msg+'",发送中...流水号:'+str(SeqID)
        
        #添加到 历史表
        
        
        try:
            sql  = "insert into\
            send_history(sqid,phone,\
            message,msgid,sendtime,pid) values('%d','%s','%s','%s','%d','%d')"%(SeqID,phone,temp_msg,str(SeqID),int(time.time()),poolID)
            db = dp.getLink()
            db.query(sql)
            dp.pushBack(db)
        except Exception ,e:
            
            print e
        
        #生成一个msgid
        t=config.GetTimeStamp()
        try:
            
            #Msg_Id
            self.socket.send(struct.pack('!10s',str(SeqID)))
            
            #Pk_total
            self.socket.send(struct.pack('!B',1))
            #Pk_number
            self.socket.send(struct.pack('!B',1))
            #Registered_Delivery
            self.socket.send(struct.pack('!B',1))
            #Msg_Fmt
            self.socket.send(struct.pack('!B',15))
            
            #ValId_Time
            self.socket.send(struct.pack('!17s',''))
            
            
            #At_Time
            self.socket.send(struct.pack('!17s',''))
            
            #DestUsr_tl
            self.socket.send(struct.pack('!I',1))
            
            #Dest_terminal_Id
            self.socket.send(struct.pack('!32s',phone))
             #Msg_Length
            self.socket.send(struct.pack('!B',length))
            
            
            #Msg_Content
            self.socket.send(struct.pack('!'+str(length)+'s',msg))
            
            
            #Msg_src
            self.socket.send(struct.pack('!21s',''))
            
            
            
            #Src_Id
            self.socket.send(struct.pack('!21s',config.ClientID))
            
            
            
            #Service_Id
            self.socket.send(struct.pack('!10s',config.serviceId))
            
            
            #LinkID

            self.socket.send(struct.pack('!20s',''))

            #Msg_level
            self.socket.send(struct.pack('!B',0))
            
            #Fee_UserType            
            self.socket.send(struct.pack('!B',0))
            
            #Fee_terminal_Id
            self.socket.send(struct.pack('!32s',''))
            #Fee_terminal_type
            self.socket.send(struct.pack('!B',0))
            #TP_pId
            self.socket.send(struct.pack('!B',0))
            #TP_udhi
            self.socket.send(struct.pack('!B',0))
            #FeeType
            self.socket.send(struct.pack('!2s',''))
            #FeeCode
            self.socket.send(struct.pack('!6s',''))
            #Dest_terminal_type
            self.socket.send(struct.pack('!B',0))
            
        except Exception,e:
            restart().start()
            return False
            print e
        app.isNotSubmit = True
        self.success = True
        return True

class recvData(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        s = app.tcp
        
        while app.recvDataFlag:
            try:
                head = s.recv(12) 
            except Exception,e:
                writeLog('db connected failed！');
                break
            if len(head)!=12:
                continue
            
            length,model,seq = struct.unpack("!III",head)
            
            try:
                body = s.recv(length-12)
            except Exception,e:
                
                continue
            data = {"length":length,"model":model,"seq":seq,"body":body}
            #加入数据接受缓冲池
            recvMsgList.put(data)
def writeLog(s,submit=True):
    fp = open("log.txt","a")
    fp.write(s+'['+time.ctime()+']'+"\r\n")
    fp.close()
def CutMsg(msg,l=2):
    '''剪切字符串，注意是unicode'''    
    length = len(msg)
    BlockNum = int(math.ceil(float(length)/l))
    result = []
    if length<=l:
        result.append(msg.encode('utf-8'))
    else:
        step=1;
        while len(msg)>0:
            if len(msg)<=l:
                result.append('(%d/%d)%s'%(step,BlockNum,msg.encode('utf-8')))
            else:
                result.append('(%d/%d)%s'%(step,BlockNum,msg[0:l].encode('utf-8')))
            msg = msg[l:]
            step = step+1
            
    return result
def sendData(s):
    '''发送数据'''
    
    while app.sendDataFlag:
        
        sql = "select id,phone,message from send_pool order by id asc limit 0,40"
        db = dp.getLink()
        msgList = db.GetAll(sql)
        dp.pushBack(db)
        
        if (msgList is not False) and len(msgList)>0:
            app.isNotSubmit = False
            for m in msgList:
                
                phoneID,phone,msg = m
                
                phone = phone.encode("utf-8")
                G_var = Global_var();
                
                if phone[0:3] not in G_var.phone and G_var.phone!='':
                    app.isNotSubmit = True
                    time.sleep(3)
                    continue
                MsgList = CutMsg(msg,65)            
                sql = 'delete from send_pool where id="%d"'%phoneID
                try:
                    db = dp.getLink()
                    db.query(sql)
                    dp.pushBack(db)
                except Exception, e:
                    print 'db search failded'+sql
                    
                for Message in MsgList:
                    sendMsgList.put({'phone':phone,'Message':Message,'phoneID':phoneID})
                    
                    app.latestActiveTime = time.time()
                    
        else:
            app.isNotSubmit = True
        
        time.sleep(3)#主暂停

#php api
def server_api(baseUrl,params):
    
    '''与php接口'''
    baseUrl+='?'
    for k,v in params.items():
        baseUrl+=k+"="+urllib.quote(v)+'&'
    backUrlList.put(baseUrl)
    

class writeBack(Thread):
    def __init__(self,url):
        Thread.__init__(self);
        self.url = url
        
    def run(self):
        try:
            
            fp = urllib.urlopen(self.url)
            
        except Exception,e:
            writeLog('error:connect failed from php：'+self.url,False)
            return False
 
class connectedTest(Thread):
    
    '''判断'''
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        return
        while True:
            
            if time.time()-app.latestActiveTime>20:
                print u'connection losed ,restart...'
                writeLog('connection losed ,restart..')
                if not app.isRestart:
                    restart().start()
            time.sleep(10)                
class ActiveTest(Thread):                
    def __init__(self,s):                
        Thread.__init__(self)
        self.s = s
    def run(self):
        while app.activeTestFlag and app.isNotSubmit:
            if sendMsgList.empty():
                try:
                    self.s.send(struct.pack('!I',12))
                    self.s.send(struct.pack('!I',8))
                    self.s.send(struct.pack('!I',GetSequenceID()))
                except Exception,e:
                    restart().start()
                    writeLog("heart package send failed")                
            time.sleep(10)
            
def getClientIp():
    myname = getfqdn(gethostname())
    myaddr = gethostbyname(myname)
    return myaddr

def setStatus(data):
    return
def setThreadFlag(v):
    app.sendDataFlag = v
    app.recvDataFlag = v
    app.connectedTestFlag = v
    app.activeTestFlag = v
    app.isNotSubmit = v
    app.latestActiveTime = time.time()
    app.br = v
    app.st = v

class command(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        
        self.clear()
        print "type 'help' or '?' for more information"
        while True:
            cmd = raw_input(">")
            command = cmd.split(" ")
            
            if command[0]=='testThread':
                self.showError()
                #self.testThread(command)
            elif command[0]=='send':
                self.sendMessage(command)
            elif command[0]=='testTcp':
                self.testTcp()
            elif command[0]=='restart':
                restart().start()
            elif command[0]=='clear':
                self.clear()
            elif command[0]=='help' or command[0]=='?':
                self.hel()
            else:
                self.showError()
    def hel(self):
        print "type 'testThread' to get current Thread infomation"
        print "type 'testTcp' to test if the tcp's connectted"
        print "type 'restart' to restart the service"
        print "type 'send PhoneNo Message' will send the number of the message,\nsuch as 'send 18221114203 wellcome'"
        print "type 'clear' to clear the screen"
        print "Thanks"
    def showError(self):
        print 'bad command'
    def clear(self):
        pass
        #os.system('cls')
    def testTcp(self):
        try:
            app.tcp.send(struct.pack('!I',12))
            app.tcp.send(struct.pack('!I',8))
            app.tcp.send(struct.pack('!I',GetSequenceID()))
            print 'tcp is OK'
        except Exception,e:
            
            print 'tcp is closed'
    def sendMessage(self,cmd):
        
        submit = SMGP_submit(app.tcp,cmd[1],cmd[2],app.db,1)
        
            
        print 'send ok'
    def testThread(self,cmd):
        if threadList.recv.isAlive():
            print "recv is ok"
        if threadList.send.isAlive():
            print "send is ok"
        
        if threadList.act.isAlive():
            print "act is ok"
class restart(Thread):
    def __init__(self):
        app.isRestart = True
        Thread.__init__(self)
    def run(self):
        setThreadFlag(False)
        try:
            print 'close socket...'
            app.tcp.shutdown(1)
            app.tcp.close()
            
            print 'server losed ,restart after 10 second'
        except Exception,e:
            print 'socket closed'
            pass

        backUrlList.put(1)
        sendMsgList.put(1)
        recvMsgList.put(1)
#        if threadList.test.isAlive():
#            threadList.test.join()
        
        if threadList.test is not None:
            print 'wait for test stop'
            if threadList.test.isAlive():
                threadList.test.join()
        if threadList.act is not None:
            print 'wait for act stop'        
            if threadList.act.isAlive():
                threadList.act.join()
        if threadList.send is not None:
            print 'wait for send stop'
            if threadList.send.isAlive():
                threadList.send.join()
        if threadList.recv is not None:
            print 'wait for recv stop'
            if threadList.recv.isAlive():
                threadList.recv.join()

        if threadList.br is not None:
            print 'wait for br stop'
            if threadList.br.isAlive():
                threadList.br.join()
        if threadList.st is not None:
            print 'wait for st stop'
            if threadList.st.isAlive():
                threadList.st.join()
        if threadList.pm is not None:
            print 'wait for pm stop'
            if threadList.pm.isAlive():
                threadList.pm.join()
        print 'all threads has stopped'
        print 'restart after 10 second .....'
        time.sleep(10)
        setThreadFlag(True)
        main()
class loginCheck(Thread):
    def __init__(self):
        app.backTime = True
        Thread.__init__(self)
    def run(self):
        index = 10
        while app.backTime:
            if index>=0:
                print index
            else:
                restart().start()
                break
            index = index-1
            time.sleep(1)

#通信队列
class backRequest(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        while True:
            if not app.br:
                break
            url = backUrlList.get()
            if url==0:
                break
            elif url==1:
                continue
            else:
                try:
                    pass
                    #print url
                    #fp = urllib.urlopen(url)
                    #data = fp.read()
                    #fp = open("urlList.txt","a")
                    #fp.write(url+"\r\n")
                    #fp.close()
                except Exception,e:
                    writeLog('error:与php通信发生错误：'+url,False)
                    return False
            time.sleep(0.2)
            
#回信队列
class processMessages(Thread):
    '''返回的消息处理'''
    def __init__(self):
        Thread.__init__(self) 
    def run(self):
        while True:
            msg = recvMsgList.get()
            if msg==0:
                break
            elif msg==1:
                break
            
            length = msg['length']
            model = msg['model']
            seq = msg['seq']
            body = msg['body']
            
            #判断类型
                #登录回显
            if model==0x80000001:
                app.latestActiveTime = time.time()
                status,auth,v,ability = struct.unpack("!I16sBI",body)
                
                if status==0:
                    print 'login success,the running number：'+str(seq)
                    app.isRestart = False
                    app.backTime = False
                    if threadList.send is None:
                        
                        threadList.send = Thread(target=sendData,args=(app.tcp,))
                        threadList.send.start()
                    
#                        threadList.test = connectedTest()
#                        threadList.test.start()
                    
                        threadList.act = ActiveTest(app.tcp)
                        threadList.act.start()
                        
                        threadList.br = backRequest()
                        threadList.br.start()


                        threadList.st = sendMsg()
                        threadList.st.start()

                        
                        command().start()
                    else:
                        try:
                            if not threadList.send.isAlive():
                                threadList.send = Thread(target=sendData,args=(app.tcp,))
                                threadList.send.start()
                        except:
                            print 1
##                        try:
##                            if not threadList.test.isAlive():
##                                threadList.test = connectedTest()
##                                threadList.test.start()
##                        except:
##                            print 2
                        try:
                            if not threadList.act.isAlive():
                                threadList.act = ActiveTest(app.tcp)
                                threadList.act.start()
                        except:
                            print 3
                        try:
                            if not threadList.br.isAlive():
                                threadList.br = backRequest()
                                threadList.br.start()
                        except:
                            print 4
                        try:
                            if not threadList.st.isAlive():
                                threadList.st = sendMsg()
                                threadList.st.start()
                        except:
                            print 5
                    
                    
                    writeLog('login success ：runing num:'+str(seq))
                else:
                    print 'login failed，error code:'+str(status)+"running num:"+str(seq)
                    writeLog('login failed,error code:'+str(status)+"running num:"+str(seq))
                #发送回显
            elif model==0x80000004:
                app.latestActiveTime = time.time()
                try:
                    au,status = struct.unpack("!10sI",body)
                    
                    if status==0:
                        
                        sql = "update send_history set status=1,msgid=%s where sqid='%d'"%(repr(au),seq)

                        db = dp.getLink()
                        db.query(sql)
                        dp.pushBack(db)
                        
                        sql = "select pid from send_history where sqid='%d' order by pid desc"%(seq,)
                    
                        try:
                            db = dp.getLink()
                            hs = db.GetAll(sql)
                            dp.pushBack(db)
                            for h in hs:
                                server_api(baseUrl="http://192.168.1.236:85/ISVService/SMSService.aspx",\
                                       params={'type':'1','id':str(h[0]),'status':'1','time':time.strftime('%Y%m%d-%H:%M:%S')})
                            

                        except Exception,e:
                            
                            writeLog(e.__str__()+'2')
                        
                        #print '短信成功发送,流水号:'+str(seq)
                        
                        writeLog('message send success,running num:'+str(seq))
                    else:
                        #频率过快
                        if str(status)=='10004':
                            app.wait = True    
                        writeLog('message send failed,error code:'+str(status)+"running num:"+str(seq))
                except:
                    writeLog('package analysis failed ,content:'+repr(body)+str(len(body)))
                #是否成功回显,和接受信息回显
            elif model==0x00000005:
                app.latestActiveTime = time.time()
                try:
                    MsgID,Dest_Id,Service_Id,TP_pid,TP_udhi,MsgFormat,Src_terminal_Id,Src_terminal_type,IsReport,MsgLength = struct.unpack("!10s21s10sBBB32sBBB",body[:79])
                    MsgContent,LinkID = struct.unpack(""+str(MsgLength)+"s20s",body[79:])
                except:
                    writeLog('package analysis failed'+repr(body))
                    continue
                
                if IsReport==1:
                    a1,a2,a3,a4,a5,seqid = struct.unpack("!10s7s10s10s32sI",MsgContent)
                    
                    
                    
                    sql = "update send_history set status=2,recvtime='%s' where sqid='%d' and status=1 "%(int(time.time()),seqid)
                    db = dp.getLink()
                    db.query(sql)
                    dp.pushBack(db)
                    
                    #回写获取pid
                    
                    sql = "select pid from send_history where msgid=%s order by pid desc"%(repr(MsgID),)
                        
                    
                    db = dp.getLink()
                    hs = db.GetAll(sql)
                    dp.pushBack(db)
                    
                    for h in hs:
                        if h is not False:
                            server_api(baseUrl="http://192.168.1.236:85/ISVService/SMSService.aspx",\
                                       params={'type':'2','id':str(h[0]),'status':'1','time':time.strftime('%Y%m%d-%H:%M:%S')})
                    #print '流水号为'+str(seqid)+'短消息已经成功发送到用户手机！'
                    
                else:
                    #print hex(MsgID)
                    try:
                        #判断编码类型
                        
                        if MsgFormat==0:
                            RecvMessage =  MsgContent.decode("ASCII").encode("utf-8")
                        elif MsgFormat==8:
                            
                            RecvMessage = MsgContent.decode("UTF-16-be").encode("utf-8")
                        elif MsgFormat==15:
                            RecvMessage = MsgContent.decode("GBK").encode("utf-8")
                        print "reciv message:"+RecvMessage+"from:"+Src_terminal_Id.strip('\x00')
                        #存进数据库   
                        try:
                           
                            #存进本地数据库
                            sql = "insert into recv_message(phone,message,dateline) \
    values('%s','%s','%d')"%(Src_terminal_Id.strip('\x00'),RecvMessage,int(time.time()))
                            db = dp.getLink()
                            db.query(sql)
                            dp.pushBack(db)
                            
                        except Exception,e:
                            print e
                    except Exception,e:
                        print e
                        print MsgContent
                #心跳回显
            elif model==0x80000008:
                app.latestActiveTime = time.time()
                
            elif model==0x80000002:
                print 'log out success'
                app.latestActiveTime = time.time()
            else:
                writeLog(repr(body))
            
            
            
                 
#发信队列
class sendMsg(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        while True:
            if app.wait:
                print 'send busy ，wait for 10 sencods...'
                time.sleep(10)
                app.wait = False
            if not app.st:
                break
            msg = sendMsgList.get()
            if msg==0:
                break
            elif msg==1:
                continue
            else:
                try:
                    submit = SMGP_submit(app.tcp,msg['phone'],msg['Message'],app.db,msg['phoneID'])
                    app.latestActiveTime = time.time()                    
                    time.sleep(0.2)
                except Exception,e:
                    writeLog(e.__str__()+'send message failed！ line 921')
                    return False
            
def main():
    G_var = Global_var()        
    try:
        tcpCliSock  =  socket(AF_INET, SOCK_STREAM)
        print 'connect server...'
        writeLog("connect server")
        tcpCliSock.connect(G_var.addr)
        print 'connect success...'
        writeLog("connect success")
        app.tcp = tcpCliSock
    except Exception,e:
        print 'connect server failed'
        writeLog("connect server failed")
    
    
    
    app.latestActiveTime = time.time()
    print 'login....'
    #login
    login = SMGP_login(tcpCliSock)
    login.login()
    
    print 'start the message recv thread'
    try:
        threadList.recv = recvData()
        threadList.recv.start()
        
        #消息处理队列
        threadList.pm = processMessages()
        threadList.pm.start()
    except Exception,e:
        print e.__str__()

# 数据库连接池
dp = dbPool()    
main()
