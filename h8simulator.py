# -*- coding: utf-8 -*-

class H8simulator :
  def __init__(self) :

    # S-Format解析時に得られるデータやメモリやレジスタ，エントリポイントなど
    # メモリ（S-Format解析時に得られるデータ．今回の場合，実装の都合で辞書型を用いる）
    self.memory = {}

    # 汎用レジスタ
    self.regulerRegisters = [0 for x in range(8)]

    # プログラムカウンタ
    self.programCounter = 0

    # コンディションコードレジスタ
    # 8ビットまとめてアクセスする場合はgetConditionCodeとsetConditionCodeを使う（未実装）
    self.conditionCodeI = False
    self.conditionCodeUI = False
    self.conditionCodeH = False
    self.conditionCodeU = False
    self.conditionCodeN = False
    self.conditionCodeZ = False
    self.conditionCodeV = False
    self.conditionCodeC = False
    
    # 状態を表す．run, sleepがあるが、状態遷移など（未実装）
    self.state = "run"

    # これより下は1命令解析ごとに使う内部変数
    # matchinstructionformatを実行後参照することができる
    # matchInstructionFormatでフォーマットに一致した場合，フォーマットのバイト数が格納される
    self.format_size = 0

    # stepを実行後，参照することができる
    # オペレーションのニーモニック("ADD", "JMP", など)
    self.operation_mnemonic = ""

    # 命令サイズ
    self.opecode_size = 0

    # オペランドサイズ(B,W,L)
    self.operand_size = ""

    # オペランドに関する情報
    #   オペランドの値，
    #   ディスプレースメント，
    #   アドレッシング，
    #   実行アドレス，
    #   オペランドのニーモニック
    self.operands = {'src':{'value':0,
                            'disp':0,
                            'addressing':"",
                            'effective_address':0,
                            'mnemonic':""},
                     'dst':{'value':0,
                            'disp':0,
                            'addressing':"",
                            'effective_address':0,
                            'mnemonic':""}}
    
    # 実際に計算されるときの右辺値と左辺値，計算結果
    self.right_side_value = 0
    self.left_side_value = 0
    self.result = 0

  def setProgramCounter(self, value) :
    self.programCounter = (value & 0xffffff)

  def getProgramCounter(self) :
    return self.programCounter

  def getConditionCode(self) :
    return ((int(self.conditionCodeI)<<7)
           +(int(self.conditionCodeUI)<<6)
           +(int(self.conditionCodeH)<<5)
           +(int(self.conditionCodeU)<<4)
           +(int(self.conditionCodeN)<<3)
           +(int(self.conditionCodeZ)<<2)
           +(int(self.conditionCodeV)<<1)
           +int(self.conditionCodeC))

  def setConditionCode(self, value) :
    self.conditionCodeI = bool((value>>7)&1)
    self.conditionCodeUI = bool((value>>6)&1)
    self.conditionCodeH = bool((value>>5)&1)
    self.conditionCodeU = bool((value>>4)&1)
    self.conditionCodeN = bool((value>>3)&1)
    self.conditionCodeZ = bool((value>>2)&1)
    self.conditionCodeV = bool((value>>1)&1)
    self.conditionCodeC = bool(value&1)

  def addToProgramCounter(self, value) :
    self.setProgramCounter(self.getProgramCounter()+value)
  
  def setStackPointer(self, value) :
    self.regulerRegisters[7] = (value & 0xffffff)

  def getStackPointer(self) :
    return self.regulerRegisters[7]

  def addToStackPointer(self, value) :
    self.set32bitRegistor(7, self.get32bitRegistor(7)+value)

  def set8bitRegistor(self, n, value) :
    if (n>>3)&1 :
      self.regulerRegisters[0x7&n] = ((0xffffff00 & self.regulerRegisters[0x7&n])
                                     |(0x000000ff & value))
    else :
      self.regulerRegisters[0x7&n] = ((0xffff00ff & self.regulerRegisters[0x7&n])
                                     |(0x0000ff00 & (value<<8)))

  def set16bitRegistor(self, n, value) :
    if (n>>3)&1 :
      self.regulerRegisters[0x7&n] = ((0x0000ffff & self.regulerRegisters[0x7&n])
                                     |(0xffff0000 & (value<<16)))
    else :
      self.regulerRegisters[0x7&n] = ((0xffff0000 & self.regulerRegisters[0x7&n])
                                     |(0x0000ffff & value))

  def set32bitRegistor(self, n, value) :
    self.regulerRegisters[n] = value
    self.regulerRegisters[n] &= 0xffffffff

  def setRegistor(self, n, value) :
    if self.operand_size == "L" :
      self.set32bitRegistor(n, value)
    elif self.operand_size == "W" :
      self.set16bitRegistor(n, value)
    elif self.operand_size == "B" :
      self.set8bitRegistor(n, value)

  def add32bitRegistor(self, n, value) :
    self.set32bitRegistor(n, self.get32bitRegistor(n)+value)

  def get8bitRegistor(self, n) :
    if (n>>3)&1 :
      value = 0xff & self.regulerRegisters[0x07&n]
    else :
      value = 0xff & (self.regulerRegisters[0x07&n]>>8)
    return value

  def get16bitRegistor(self, n) :
    if ((n>>3)&1) == 0 :
      value = 0xffff & self.regulerRegisters[0x07&n]
    else :
      value = 0xffff & (self.regulerRegisters[0x07&n]>>16)
    return value

  def get32bitRegistor(self, n) :
    return 0xffffffff & self.regulerRegisters[n]

  def getRegistor(self, n) :
    if self.operand_size == "L" :
      return self.get32bitRegistor(n)
    elif self.operand_size == "W" :
      return self.get16bitRegistor(n)
    elif self.operand_size == "B" :
      return self.get8bitRegistor(n)

  def get8bitMemory(self, n) :
    return self.memory[n]

  def get16bitMemory(self, n) :
    return (self.memory[n]
           +(self.memory[n+1]<<8))

  def get32bitMemory(self, n) :
    value = (self.memory[n]
            +(self.memory[n+1]<<8)
            +(self.memory[n+2]<<16)
            +(self.memory[n+2]<<24))
    return value

  def getMemory(self, n) :
    if self.operand_size == "L" :
      return self.get32bitMemory(n)
    elif self.operand_size == "W" :
      return self.get16bitMemory(n)
    elif self.operand_size == "B" :
      return self.get8bitMemory(n)

  def set8bitMemory(self, n, value) :
    self.memory[n] = value & 0xff

  def set16bitMemory(self, n, value) :
    self.memory[n] = value & 0xff
    self.memory[n+1] = (value>>8) & 0xff

  def set32bitMemory(self, n, value) :
    self.memory[n] = value & 0xff
    self.memory[n+1] = (value>>8) & 0xff
    self.memory[n+2] = (value>>16) & 0xff
    self.memory[n+3] = (value>>24) & 0xff

  def setMemory(self, n, value) :
    if self.operand_size == "L" :
      self.set32bitMemory(n, value)
    elif self.operand_size == "W" :
      self.set16bitMemory(n, value)
    elif self.operand_size == "B" :
      self.set8bitMemory(n, value)

  def pushStack(self, value) :
    self.addToStackPointer(-4)
    self.set32bitMemory(self.getStackPointer(), value)

  def popStack(self) :
    value = self.get32bitMemory(self.getStackPointer())
    self.addToStackPointer(4)
    return value

  def getSource(self) :
    if self.operands['src']['addressing'] == 'immidiate' :
      return self.operands['src']['value']
    elif self.operands['src']['addressing'] == 'impliedImmidiate' :
      return self.operands['src']['value']
    elif self.operands['src']['addressing'] == 'register' :
      return self.getRegistor(self.operands['src']['value'])
    else :
      return self.getMemory(self.operands['src']['effective_address'])

  def getDestination(self) :
    if self.operands['dst']['addressing'] == 'immidiate' :
      return self.operands['dst']['value']
    elif self.operands['dst']['addressing'] == 'impliedImmidiate' :
      return self.operands['dst']['value']
    elif self.operands['dst']['addressing'] == 'register' :
      return self.getRegistor(self.operands['dst']['value'])
    else :
      return self.getMemory(self.operands['dst']['effective_address'])

  def setDestination(self, value) :
    if self.operands['dst']['addressing'] == 'register' :
      self.setRegistor(self.operands['dst']['value'], value)
    else :
      self.setMemory(self.operands['dst']['effective_address'], value)

  def getMnemonic(self) :
    mnemonic = self.operation_mnemonic.lower()
    if self.operand_size != None :
      mnemonic += '.' + self.operand_size.lower()
    if self.operands['src']['addressing'] != None :
      mnemonic += ' ' + self.operands['src']['mnemonic']
    if self.operands['dst']['addressing'] != None :
      mnemonic += ',' + self.operands['dst']['mnemonic']
    return mnemonic

  def decodeOpecode(self) :
    self.operand_size = None
    self.operands['src']['addressing'] = None
    self.operands['dst']['addressing'] = None

    if ( self.matchInstructionFormat("8***") or 
         self.matchInstructionFormat("9***") or
         self.matchInstructionFormat("e***") or
         self.matchInstructionFormat("a***") or
         self.matchInstructionFormat("f***") or
         self.matchInstructionFormat("c***") or
         self.matchInstructionFormat("b***") or
         self.matchInstructionFormat("d***") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = self.memory[self.programCounter+1]
      self.operands['src']['addressing'] = "immidiate"
      self.operands['dst']['value'] = self.memory[self.programCounter]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif ( self.matchInstructionFormat("08**") or
           self.matchInstructionFormat("0e**") or
           self.matchInstructionFormat("16**") or
           self.matchInstructionFormat("1c**") or
           self.matchInstructionFormat("51**") or
           self.matchInstructionFormat("0c**") or
           self.matchInstructionFormat("50**") or
           self.matchInstructionFormat("14**") or
           self.matchInstructionFormat("18**") or
           self.matchInstructionFormat("1e**") or
           self.matchInstructionFormat("15**") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif ( self.matchInstructionFormat("791*****") or
           self.matchInstructionFormat("796*****") or
           self.matchInstructionFormat("792*****") or
           self.matchInstructionFormat("790*****") or
           self.matchInstructionFormat("794*****") or
           self.matchInstructionFormat("793*****") or
           self.matchInstructionFormat("795*****") ) :
      self.operand_size = "W"
      self.operands['src']['value'] = ((self.memory[self.programCounter+2]<<8)
                                      +self.memory[self.programCounter+3])
      self.operands['src']['addressing'] = "immidiate"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif ( self.matchInstructionFormat("09**") or
           self.matchInstructionFormat("66**") or
           self.matchInstructionFormat("1d**") or
           self.matchInstructionFormat("0d**") or
           self.matchInstructionFormat("64**") or
           self.matchInstructionFormat("19**") or
           self.matchInstructionFormat("65**") ) :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif ( self.matchInstructionFormat("7a1[0***]********") or
           self.matchInstructionFormat("7a6[0***]********") or
           self.matchInstructionFormat("7a2[0***]********") or
           self.matchInstructionFormat("7a0[0***]********") or
           self.matchInstructionFormat("7a4[0***]********") or
           self.matchInstructionFormat("7a3[0***]********") or
           self.matchInstructionFormat("7a5[0***]********") ) :
      self.operand_size = "L"
      self.operands['src']['value'] = ((self.memory[self.programCounter+2]<<24)
                                      +(self.memory[self.programCounter+3]<<16)
                                      +(self.memory[self.programCounter+4]<<8)
                                      +self.memory[self.programCounter+5])
      self.operands['src']['addressing'] = "immidiate"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x07
      self.operands['dst']['addressing'] = "register"

    elif ( self.matchInstructionFormat("0a[1***0***]") or
           self.matchInstructionFormat("1f[1***0***]") or
           self.matchInstructionFormat("0f[1***0***]") or
           self.matchInstructionFormat("1a[1***0***]") ) :
      self.operand_size = "L"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x07
      self.operands['dst']['addressing'] = "register"

    elif ( self.matchInstructionFormat("1b7[0***]") or
           self.matchInstructionFormat("1bf[0***]") or
           self.matchInstructionFormat("17f[0***]") or
           self.matchInstructionFormat("177[0***]") or
           self.matchInstructionFormat("0b7[0***]") or
           self.matchInstructionFormat("0bf[0***]") or
           self.matchInstructionFormat("17b[0***]") or
           self.matchInstructionFormat("173[0***]") or
           self.matchInstructionFormat("12b[0***]") or
           self.matchInstructionFormat("13b[0***]") or
           self.matchInstructionFormat("123[0***]") or
           self.matchInstructionFormat("133[0***]") or
           self.matchInstructionFormat("10b[0***]") or
           self.matchInstructionFormat("11b[0***]") or
           self.matchInstructionFormat("103[0***]") or
           self.matchInstructionFormat("113[0***]") ) :
      self.operand_size = "L"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x07
      self.operands['dst']['addressing'] = "register"

    elif ( self.matchInstructionFormat("0b0[0***]") or
           self.matchInstructionFormat("1b0[0***]") ) :
           
      self.operand_size = "L"
      self.operands['src']['value'] = 1
      self.operands['src']['addressing'] = "impliedImmidiate"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x07
      self.operands['dst']['addressing'] = "register"

    elif ( self.matchInstructionFormat("0b8[0***]") or
           self.matchInstructionFormat("1b8[0***]") ) :
           
      self.operand_size = "L"
      self.operands['src']['value'] = 2
      self.operands['src']['addressing'] = "impliedImmidiate"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x07
      self.operands['dst']['addressing'] = "register"

    elif ( self.matchInstructionFormat("0b9[0***]") or
           self.matchInstructionFormat("1b9[0***]") ) :
      self.operand_size = "L"
      self.operands['src']['value'] = 4
      self.operands['src']['addressing'] = "impliedImmidiate"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x07
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("010069[0***0***]") :
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['addressing'] = "registerIndirect"
      self.operands['dst']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['dst']['addressing'] = "register"

    elif ( self.matchInstructionFormat("01f066[0***0***]") or
           self.matchInstructionFormat("01f064[0***0***]") or
           self.matchInstructionFormat("01f065[0***0***]") ) :
      self.operand_size = "L"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("01006d[0***0***]") :
      self.operand_size = "L"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['addressing'] = "registerIndirectIncrement"
      self.operands['dst']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("010069[1***0***]") :
      self.operand_size = "L"
      self.operands['src']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['dst']['addressing'] = "registerIndirect"

    elif self.matchInstructionFormat("01006d[1***0***]") :
      self.operand_size = "L"
      self.operands['src']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['dst']['addressing'] = "registerindirectDecrement"

    elif ( self.matchInstructionFormat("06**") or
           self.matchInstructionFormat("07**") or
           self.matchInstructionFormat("05**") or
           self.matchInstructionFormat("04**") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = self.memory[self.programCounter+1]
      self.operands['src']['addressing'] = "register"

    elif ( self.matchInstructionFormat("76[0***]*") or
           self.matchInstructionFormat("72[0***]*") or
           self.matchInstructionFormat("76[1***]*") or
           self.matchInstructionFormat("77[0***]*") or
           self.matchInstructionFormat("74[1***]*") or
           self.matchInstructionFormat("67[1***]*") or
           self.matchInstructionFormat("75[1***]*") or
           self.matchInstructionFormat("77[1***]*") or
           self.matchInstructionFormat("71[0***]*") or
           self.matchInstructionFormat("61[0***]*") or
           self.matchInstructionFormat("74[0***]*") or
           self.matchInstructionFormat("70[0***]*") or
           self.matchInstructionFormat("67[0***]*") or
           self.matchInstructionFormat("73[0***]*") or
           self.matchInstructionFormat("75[0***]*") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['src']['addressing'] = "immidiate"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif (self.matchInstructionFormat("7c[0***]076[0***]0") or
          self.matchInstructionFormat("7d[0***]072[0***]0") or
          self.matchInstructionFormat("7c[0***]076[1***]0") or
          self.matchInstructionFormat("7c[0***]077[1***]0") or
          self.matchInstructionFormat("7c[0***]074[1***]0") or
          self.matchInstructionFormat("7d[0***]067[1***]0") or
          self.matchInstructionFormat("7c[0***]075[1***]0") or
          self.matchInstructionFormat("7c[0***]077[0***]0") or
          self.matchInstructionFormat("7d[0***]071[0***]0") or
          self.matchInstructionFormat("7c[0***]074[0***]0") or
          self.matchInstructionFormat("7d[0***]070[0***]0") or
          self.matchInstructionFormat("7d[0***]067[0***]0") or
          self.matchInstructionFormat("7c[0***]073[0***]0") or
          self.matchInstructionFormat("7c[0***]075[0***]0") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['addressing'] = "immidiate"
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['addressing'] = "register"

    elif (self.matchInstructionFormat("7e**76[0***]0") or
          self.matchInstructionFormat("7f**72[0***]0") or
          self.matchInstructionFormat("7e**76[1***]0") or
          self.matchInstructionFormat("7e**77[1***]0") or
          self.matchInstructionFormat("7e**74[1***]0") or
          self.matchInstructionFormat("7f**67[1***]0") or
          self.matchInstructionFormat("7e**75[1***]0") or
          self.matchInstructionFormat("7e**77[0***]0") or
          self.matchInstructionFormat("7f**71[0***]0") or
          self.matchInstructionFormat("7e**74[0***]0") or
          self.matchInstructionFormat("7f**70[0***]0") or
          self.matchInstructionFormat("7f**67[0***]0") or
          self.matchInstructionFormat("7e**73[0***]0") or
          self.matchInstructionFormat("7e**75[0***]0") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['addressing'] = "immidiate"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]
      self.operands['src']['addressing'] = "absolute8"

    elif (self.matchInstructionFormat("40**") or
          self.matchInstructionFormat("41**") or
          self.matchInstructionFormat("42**") or
          self.matchInstructionFormat("43**") or
          self.matchInstructionFormat("44**") or
          self.matchInstructionFormat("45**") or
          self.matchInstructionFormat("46**") or
          self.matchInstructionFormat("47**") or
          self.matchInstructionFormat("48**") or
          self.matchInstructionFormat("49**") or
          self.matchInstructionFormat("4a**") or
          self.matchInstructionFormat("4b**") or
          self.matchInstructionFormat("4c**") or
          self.matchInstructionFormat("4d**") or
          self.matchInstructionFormat("4e**") or
          self.matchInstructionFormat("4f**") or
          self.matchInstructionFormat("55**") ) :
      self.operand_size = "B"
      self.operands['src']['disp'] = self.memory[self.programCounter+1]
      self.operands['src']['addressing'] = "pcRelative8"

    elif (self.matchInstructionFormat("5800****") or
          self.matchInstructionFormat("5810****") or
          self.matchInstructionFormat("5820****") or
          self.matchInstructionFormat("5830****") or
          self.matchInstructionFormat("5840****") or
          self.matchInstructionFormat("5850****") or
          self.matchInstructionFormat("5860****") or
          self.matchInstructionFormat("5870****") or
          self.matchInstructionFormat("5880****") or
          self.matchInstructionFormat("5890****") or
          self.matchInstructionFormat("58a0****") or
          self.matchInstructionFormat("58b0****") or
          self.matchInstructionFormat("58c0****") or
          self.matchInstructionFormat("58d0****") or
          self.matchInstructionFormat("58*0****") or
          self.matchInstructionFormat("58f0****") or
          self.matchInstructionFormat("5c00****") ) :
      self.operand_size = "W"
      self.operands['src']['disp'] = ((self.memory[self.programCounter+2]<<8)
                                     +self.memory[self.programCounter+3])
      self.operands['src']['addressing'] = "pcRelative16"

    elif (self.matchInstructionFormat("62**") or
          self.matchInstructionFormat("61**") or
          self.matchInstructionFormat("60**") or
          self.matchInstructionFormat("63**") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif (self.matchInstructionFormat("7d[0***]062*0") or
          self.matchInstructionFormat("7d[0***]061*0") or
          self.matchInstructionFormat("7d[0***]060*0") or
          self.matchInstructionFormat("7c[0***]063*0") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['addressing'] = "registerIndirect"

    elif (self.matchInstructionFormat("7f**62*0") or
          self.matchInstructionFormat("7f**61*0") or
          self.matchInstructionFormat("7f**60*0") or
          self.matchInstructionFormat("7e**63*0") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]
      self.operands['dst']['addressing'] = "absolute8"

    elif (self.matchInstructionFormat("0f0*") or
          self.matchInstructionFormat("1a0*") or
          self.matchInstructionFormat("1f0*") or
          self.matchInstructionFormat("0a0*") or
          self.matchInstructionFormat("030*") or
          self.matchInstructionFormat("178*") or
          self.matchInstructionFormat("170*") or
          self.matchInstructionFormat("128*") or
          self.matchInstructionFormat("138*") or
          self.matchInstructionFormat("120*") or
          self.matchInstructionFormat("130*") or
          self.matchInstructionFormat("108*") or
          self.matchInstructionFormat("118*") or
          self.matchInstructionFormat("100*") or
          self.matchInstructionFormat("110*") or
          self.matchInstructionFormat("020*") ) :
      self.operand_size = "B"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif (self.matchInstructionFormat("1b5*") or
          self.matchInstructionFormat("1bd*") or
          self.matchInstructionFormat("17d*") or
          self.matchInstructionFormat("175*") or
          self.matchInstructionFormat("0b5*") or
          self.matchInstructionFormat("0bd*") or
          self.matchInstructionFormat("179*") or
          self.matchInstructionFormat("171*") or
          self.matchInstructionFormat("6d7*") or
          self.matchInstructionFormat("6df*") or
          self.matchInstructionFormat("129*") or
          self.matchInstructionFormat("139*") or
          self.matchInstructionFormat("121*") or
          self.matchInstructionFormat("131*") or
          self.matchInstructionFormat("109*") or
          self.matchInstructionFormat("101*") or
          self.matchInstructionFormat("111*") or
          self.matchInstructionFormat("119*") ) :
      self.operand_size = "W"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif (self.matchInstructionFormat("01d051**") or
          self.matchInstructionFormat("01c050**") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+3]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif (self.matchInstructionFormat("01d053*[0***]") or
          self.matchInstructionFormat("01c052*[0***]") ) :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+3]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif (self.matchInstructionFormat("53*[0***]") or
          self.matchInstructionFormat("52*[0***]") ) :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif (self.matchInstructionFormat("7b5c598f") or
          self.matchInstructionFormat("7bd4598f") or
          self.matchInstructionFormat("0000") or
          self.matchInstructionFormat("5670") or
          self.matchInstructionFormat("5470") or
          self.matchInstructionFormat("0180") ) :
      pass

    elif (self.matchInstructionFormat("59[0***]0") or
          self.matchInstructionFormat("5d[0***]0") ) :
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['src']['addressing'] = "registerIndirect"

    elif (self.matchInstructionFormat("5a******") or
          self.matchInstructionFormat("5e******") ) :
      self.operands['src']['value'] = ((self.memory[self.programCounter+1]<<16)
                                      +(self.memory[self.programCounter+2]<<8)
                                      +self.memory[self.programCounter+3])
      self.operands['src']['addressing'] = "absolute24"

    elif (self.matchInstructionFormat("5b**") or
          self.matchInstructionFormat("5f**") ) :
      self.operands['src']['value'] = self.memory[self.programCounter+1]
      self.operands['src']['addressing'] = "memoryIndirect"

    elif (self.matchInstructionFormat("014069[0***]0") or
          self.matchInstructionFormat("014069[1***]0") or
          self.matchInstructionFormat("01406d[1***]0") ) :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['addressing'] = "registerIndirect"

    elif self.matchInstructionFormat("01406d[0***]0") :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['addressing'] = "registerIndirectIncrement"

    elif (self.matchInstructionFormat("01406f[0***]0****") or
          self.matchInstructionFormat("01406f[1***]0****") ) :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['disp'] = ((self.memory[self.programCounter+4]<<8)
                                      +self.memory[self.programCounter+5])
      self.operands['src']['addressing'] = "registerIndirectDisplacement16"

    elif (self.matchInstructionFormat("014078[0***]06b2000******") or
          self.matchInstructionFormat("014078[0***]06ba000******") ) :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['disp'] = ((self.memory[self.programCounter+7]<<16)
                    +(self.memory[self.programCounter+8]<<8)
                    +self.memory[self.programCounter+9])
      self.operands['src']['addressing'] = "registerIndirectDisplacement24"

    elif (self.matchInstructionFormat("01406b00****") or
          self.matchInstructionFormat("01406b80****") ) :
      self.operand_size = "W"
      self.operands['src']['value'] = ((self.memory[self.programCounter+4]<<8)
                                       +self.memory[self.programCounter+5])
      self.operands['src']['addressing'] = "absolute16"

    elif (self.matchInstructionFormat("01406b2000******") or
          self.matchInstructionFormat("01406ba000******") ) :
      self.operand_size = "W"
      self.operands['src']['value'] = ((self.memory[self.programCounter+5]<<16)
               +(self.memory[self.programCounter+6]<<8)
               +self.memory[self.programCounter+7])
      self.operands['src']['addressing'] = "absolute24"

    elif self.matchInstructionFormat("68[0***]*") :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['src']['addressing'] = "registerIndirect"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("6c[0***]*") :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['src']['addressing'] = "registerIndirectIncrement"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("6e[0***]*****") :
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['src']['disp'] = ((self.memory[self.programCounter+2]<<8)
                                      +self.memory[self.programCounter+3])
      self.operands['src']['addressing'] = "registerIndirectDisplacement16"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("78[0***]06a2*00******") : 
      self.operand_size = "B"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['src']['disp'] = ((self.memory[self.programCounter+5]<<16)
                                     +(self.memory[self.programCounter+6]<<8)
                                     +self.memory[self.programCounter+7])
      self.operands['src']['addressing'] = "registerIndirectDisplacement24"
      self.operands['dst']['value'] = self.memory[self.programCounter+3]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("2***") :
      self.operand_size = "B"
      self.operands['src']['value'] = self.memory[self.programCounter+1]
      self.operands['src']['addressing'] = "absolute8"
      self.operands['dst']['value'] = self.memory[self.programCounter]&0x0f
      self.operands['src']['addressing'] = "register"
      
    elif (self.matchInstructionFormat("6a0*****") or
          self.matchInstructionFormat("6a4*****") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = ((self.memory[self.programCounter+2]<<8)
                                       +self.memory[self.programCounter+3])
      self.operands['src']['addressing'] = "absolute16"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("6a2*********") :
      self.operand_size = "B"
      self.operands['src']['value'] = ((self.memory[self.programCounter+2]<<16)
                                      +(self.memory[self.programCounter+3]<<8)
                                      +self.memory[self.programCounter+4])
      self.operands['src']['addressing'] = "absolute24"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("68[1***]*") :
      self.operand_size = "B"
      self.operands['src']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['addressing'] = "registerindirect"
      
    elif self.matchInstructionFormat("6c[1***]*") :
      self.operand_size = "B"
      self.operands['src']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['addressing'] = "registerIndirectDecrement"

    elif self.matchInstructionFormat("6e[1***]*****") :
      self.operand_size = "B"
      self.operands['src']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['disp'] = ((self.memory[self.programCounter+2]<<8)
                                      +self.memory[self.programCounter+3])
      self.operands['dst']['addressing'] = "registerIndirectDisplacement16"

    elif self.matchInstructionFormat("78[0***]06aa*00******") :
      self.operand_size = "B"
      self.operands['src']['value'] = self.memory[self.programCounter+3]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['disp'] = ((self.memory[self.programCounter+5]<<16)
                                     +(self.memory[self.programCounter+6]<<8)
                                     +self.memory[self.programCounter+7])
      self.operands['dst']['addressing'] = "registerIndirectDisplacement24"

    elif self.matchInstructionFormat("3***") : 
      self.operand_size = "B"
      self.operands['src']['value'] = self.memory[self.programCounter]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]
      self.operands['dst']['addressing'] = "absolute8"

    elif (self.matchInstructionFormat("6a8*****") or
          self.matchInstructionFormat("6ac*****") ) :
      self.operand_size = "B"
      self.operands['src']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = ((self.memory[self.programCounter+2]<<8)
                                      +self.memory[self.programCounter+3])
      self.operands['dst']['addressing'] = "absolute16"

    elif self.matchInstructionFormat("6aa*00******") :
      self.operand_size = "B"
      self.operands['src']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = ((self.memory[self.programCounter+3]<<16)
                                      +(self.memory[self.programCounter+4]<<8)
                                      +self.memory[self.programCounter+5])
      self.operands['dst']['addressing'] = "absolute24"

    elif self.matchInstructionFormat("69[0***]*") :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['addressing'] = "registerIndirect"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("6d[0***]*") :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['addressing'] = "registerIndirectIncrement"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("6f[0***]*****") :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['src']['disp'] = ((self.memory[self.programCounter+2]<<8)
                                     +self.memory[self.programCounter+3])
      self.operands['src']['addressing'] = "registerIndirectDisplacement16"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("78[0***]06b2*00******") :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['src']['disp'] = ((self.memory[self.programCounter+5]<<16)
                                      +(self.memory[self.programCounter+6]<<8)
                                      +self.memory[self.programCounter+7])
      self.operands['src']['addressing'] = "registerindirectdisplacement24"
      self.operands['dst']['value'] = self.memory[self.programCounter+3]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("6b0*****") :
      self.operand_size = "W"
      self.operands['src']['value'] = ((self.memory[self.programCounter+2]<<8)
                                      +self.memory[self.programCounter+3])
      self.operands['src']['addressing'] = "registerIndirectIncrement"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("6b2*00******") :
      self.operand_size = "W"
      self.operands['src']['value'] = ((self.memory[self.programCounter+3]<<16)
               +(self.memory[self.programCounter+4]<<8)
               +self.memory[self.programCounter+5])
      self.operands['src']['addressing'] = "absolute24"
      self.operands['dst']['value'] = self.memory[self.programCounter+1]&0x08
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("69[1***]*") :
      self.operand_size = "W"
      self.operands['src']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['addressing'] = "registerIndirect"

    elif self.matchInstructionFormat("6d[1***]*") :
      self.operand_size = "W"
      self.operands['src']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['addressing'] = "registerindirectDecrement"

    elif self.matchInstructionFormat("6f[1***]*****") :
      self.operand_size = "W"
      self.operands['src']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['disp'] = ((self.memory[self.programCounter+2])<<8
                    +self.memory[self.programCounter+3])
      self.operands['dst']['addressing'] = "registerIndirectDisplacement16"

    elif self.matchInstructionFormat("78[0***]06ba*00******") :
      self.operand_size = "W"
      self.operands['src']['value'] = self.memory[self.programCounter+3]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+1]>>4)&0x07
      self.operands['dst']['disp'] = ((self.memory[self.programCounter+5]<<16)
                    +(self.memory[self.programCounter+6]<<8)
                    +self.memory[self.programCounter+7])
      self.operands['dst']['addressing'] = "registerIndirectDisplacement24"

    elif self.matchInstructionFormat("6b8*******") :
      self.operand_size = "W"
      self.operands['src']['value'] = (self.memory[self.programCounter+1]&0x0f)
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = ((self.memory[self.programCounter+2]<<8)
               +self.memory[self.programCounter+3])
      self.operands['dst']['addressing'] = "absolute16"

    elif self.matchInstructionFormat("6ba*00******") :
      self.operand_size = "W"
      self.operands['src']['value'] = self.memory[self.programCounter+1]&0x0f
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = ((self.memory[self.programCounter+3]<<16)
               +(self.memory[self.programCounter+4]<<8)
               +self.memory[self.programCounter+5])
      self.operands['dst']['addressing'] = "absolute24"
                               
    elif self.matchInstructionFormat("01006f[0***0***]****") :
      self.operand_size = "L"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['disp'] = ((self.memory[self.programCounter+4]<<8)
                                     +self.memory[self.programCounter+5])
      self.operands['src']['addressing'] = "registerIndirectDisplacement16"
      self.operands['dst']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("010078[0***]06b2[0***]00******") :
      self.operand_size = "L"
      self.operands['src']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['src']['disp'] = ((self.memory[self.programCounter+7]<<16)
                                     +(self.memory[self.programCounter+8]<<8)
                                     +self.memory[self.programCounter+9])
      self.operands['src']['addressing'] = "registerindirectdisplacement24"
      self.operands['dst']['value'] = self.memory[self.programCounter+5]&0x07
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("01006b0[0***]****") :
      self.operand_size = "L"
      self.operands['src']['value'] = ((self.memory[self.programCounter+4]<<8)
                                      +self.memory[self.programCounter+5])
      self.operands['src']['addressing'] = "absolute16"
      self.operands['dst']['addressing'] = "register"
      self.operands['dst']['value'] = self.memory[self.programCounter+3]&0x07

    elif self.matchInstructionFormat("01006b2[0***]00******") :
      self.operand_size = "L"
      self.operands['src']['value'] = ((self.memory[self.programCounter+5]<<16)
                                      +(self.memory[self.programCounter+6]<<8)
                                      +self.memory[self.programCounter+7])
      self.operands['src']['addressing'] = "absolute24"
      self.operands['dst']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['dst']['addressing'] = "register"

    elif self.matchInstructionFormat("01006f[1***0***]****") :
      self.operand_size = "L"
      self.operands['src']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['dst']['disp'] = ((self.memory[self.programCounter+4]<<8)
                                     +self.memory[self.programCounter+5])
      self.operands['dst']['addressing'] = "registerIndirectDisplacement16"

    elif self.matchInstructionFormat("010078[1***]06ba[0***]00******") :
      self.operand_size = "L"
      self.operands['src']['value'] = self.memory[self.programCounter+5]&0x07
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = (self.memory[self.programCounter+3]>>4)&0x07
      self.operands['dst']['disp'] = ((self.memory[self.programCounter+7]<<16)
                                     +(self.memory[self.programCounter+8]<<8)
                                     +self.memory[self.programCounter+9])
      self.operands['dst']['addressing'] = "registerindirectdisplacement24"

    elif self.matchInstructionFormat("01006b8[0***]****") :
      self.operand_size = "L"
      self.operands['src']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = ((self.memory[self.programCounter+4]<<8)
                                      +self.memory[self.programCounter+5])
      self.operands['src']['addressing'] = "absolute16"
      
    elif self.matchInstructionFormat("01006ba[0***]00******") :
      self.operand_size = "L"
      self.operands['src']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['value'] = ((self.memory[self.programCounter+5]<<16)
                                      +(self.memory[self.programCounter+6]<<8)
                                      +self.memory[self.programCounter+7])
      self.operands['dst']['addressing'] = "absolute24"

    elif (self.matchInstructionFormat("01006d7[0***]") or
          self.matchInstructionFormat("01006df[0***]") ) :
      self.operand_size = "L"
      self.operands['src']['value'] = self.memory[self.programCounter+3]&0x07
      self.operands['src']['addressing'] = "register"
      self.operands['dst']['addressing'] = ""

    elif self.matchInstructionFormat("57[00**]0") :
      self.operands['src']['value'] = (self.memory[self.programCounter+1]>>4)&0x03
      self.operands['src']['addressing'] = "immidiate"

    self.opecode_size = self.format_size

    # オペレーションの判別
    if self.matchInstructionFormat("00") :
      self.operation_mnemonic = "NOP"
    elif self.matchInstructionFormat("02") :
      self.operation_mnemonic = "STC"
    elif self.matchInstructionFormat("03") :
      self.operation_mnemonic = "LDC"
    elif self.matchInstructionFormat("04") :
      self.operation_mnemonic = "ORC"
    elif self.matchInstructionFormat("05") :
      self.operation_mnemonic = "XORC"
    elif self.matchInstructionFormat("06") :
      self.operation_mnemonic = "ANDC"
    elif self.matchInstructionFormat("07") :
      self.operation_mnemonic = "LDC"
    elif self.matchInstructionFormat("08") :
      self.operation_mnemonic = "ADD"
    elif self.matchInstructionFormat("09") :
      self.operation_mnemonic = "ADD"
    elif self.matchInstructionFormat("0c") :
      self.operation_mnemonic = "MOV"
    elif self.matchInstructionFormat("0d") :
      self.operation_mnemonic = "MOV"
    elif self.matchInstructionFormat("0e") :
      self.operation_mnemonic = "ADDX"
    elif self.matchInstructionFormat("14") :
      self.operation_mnemonic = "OR"
    elif self.matchInstructionFormat("15") :
      self.operation_mnemonic = "XOR"
    elif self.matchInstructionFormat("16") :
      self.operation_mnemonic = "AND"
    elif self.matchInstructionFormat("18") :
      self.operation_mnemonic = "SUB"
    elif self.matchInstructionFormat("19") :
      self.operation_mnemonic = "SUB"
    elif self.matchInstructionFormat("1c") :
      self.operation_mnemonic = "CMP"
    elif self.matchInstructionFormat("1d") :
      self.operation_mnemonic = "CMP"
    elif self.matchInstructionFormat("1e") :
      self.operation_mnemonic = "CMP"
    elif self.matchInstructionFormat("2*") :
      self.operation_mnemonic = "MOV.B"
    elif self.matchInstructionFormat("3*") :
      self.operation_mnemonic = "MOV.B"
    elif self.matchInstructionFormat("40") :
      self.operation_mnemonic = "BRA"
    elif self.matchInstructionFormat("41") :
      self.operation_mnemonic = "BRN"
    elif self.matchInstructionFormat("42") :
      self.operation_mnemonic = "BHI"
    elif self.matchInstructionFormat("43") :
      self.operation_mnemonic = "BLS"
    elif self.matchInstructionFormat("44") :
      self.operation_mnemonic = "BCC"
    elif self.matchInstructionFormat("45") :
      self.operation_mnemonic = "BCS"
    elif self.matchInstructionFormat("46") :
      self.operation_mnemonic = "BNE"
    elif self.matchInstructionFormat("47") :
      self.operation_mnemonic = "BEQ"
    elif self.matchInstructionFormat("48") :
      self.operation_mnemonic = "BVC"
    elif self.matchInstructionFormat("49") :
      self.operation_mnemonic = "BVS"
    elif self.matchInstructionFormat("4a") :
      self.operation_mnemonic = "BPL"
    elif self.matchInstructionFormat("4b") :
      self.operation_mnemonic = "BMI"
    elif self.matchInstructionFormat("4c") :
      self.operation_mnemonic = "BGE"
    elif self.matchInstructionFormat("4d") :
      self.operation_mnemonic = "BLT"
    elif self.matchInstructionFormat("4e") :
      self.operation_mnemonic = "BGT"
    elif self.matchInstructionFormat("4f") :
      self.operation_mnemonic = "BLE"
    elif self.matchInstructionFormat("50") :
      self.operation_mnemonic = "MULXU"
    elif self.matchInstructionFormat("51") :
      self.operation_mnemonic = "DIVXU"
    elif self.matchInstructionFormat("52") :
      self.operation_mnemonic = "MULXU"
    elif self.matchInstructionFormat("53") :
      self.operation_mnemonic = "DIVXU"
    elif self.matchInstructionFormat("54") :
      self.operation_mnemonic = "RTS"
    elif self.matchInstructionFormat("55") :
      self.operation_mnemonic = "BSR"
    elif self.matchInstructionFormat("56") :
      self.operation_mnemonic = "RTE"
    elif self.matchInstructionFormat("57") :
      self.operation_mnemonic = "TRAPA"
    elif self.matchInstructionFormat("59") :
      self.operation_mnemonic = "JMP"
    elif self.matchInstructionFormat("5a") :
      self.operation_mnemonic = "JMP"
    elif self.matchInstructionFormat("5b") :
      self.operation_mnemonic = "JMP"
    elif self.matchInstructionFormat("5c") :
      self.operation_mnemonic = "BSR"
    elif self.matchInstructionFormat("5d") :
      self.operation_mnemonic = "JSR"
    elif self.matchInstructionFormat("5e") :
      self.operation_mnemonic = "JSR"
    elif self.matchInstructionFormat("5f") :
      self.operation_mnemonic = "JSR"
    elif self.matchInstructionFormat("60") :
      self.operation_mnemonic = "BSET"
    elif self.matchInstructionFormat("61") :
      self.operation_mnemonic = "BNOT"
    elif self.matchInstructionFormat("62") :
      self.operation_mnemonic = "BCLR"
    elif self.matchInstructionFormat("63") :
      self.operation_mnemonic = "BTST"
    elif self.matchInstructionFormat("64") :
      self.operation_mnemonic = "OR"
    elif self.matchInstructionFormat("65") :
      self.operation_mnemonic = "XOR"
    elif self.matchInstructionFormat("66") :
      self.operation_mnemonic = "AND"
    elif self.matchInstructionFormat("67") :
      if self.matchInstructionFormat("**[0***]") :
        self.operation_mnemonic = "BST"
      else :
        self.operation_mnemonic = "BIST"
    elif self.matchInstructionFormat("6[1***]") :
      self.operation_mnemonic = "MOV"
    elif self.matchInstructionFormat("70") :
      self.operation_mnemonic = "BSET"
    elif self.matchInstructionFormat("71") :
      self.operation_mnemonic = "BNOT"
    elif self.matchInstructionFormat("72") :
      self.operation_mnemonic = "BCLR"
    elif self.matchInstructionFormat("73") :
      self.operation_mnemonic = "BTST"
    elif self.matchInstructionFormat("74") :
      if self.matchInstructionFormat("**[0***]") :
        self.operation_mnemonic = "BOR"
      else :
        self.operation_mnemonic = "BIOR"
    elif self.matchInstructionFormat("75") :
      if self.matchInstructionFormat("**[0***]") :
        self.operation_mnemonic = "BXOR"
      else :
        self.operation_mnemonic = "BXIOR"
    elif self.matchInstructionFormat("76") :
      if self.matchInstructionFormat("**[0***]") :
        self.operation_mnemonic = "BAND"
      else :
        self.operation_mnemonic = "BIAND"
    elif self.matchInstructionFormat("77") :
      if self.matchInstructionFormat("**[0***]") :
        self.operation_mnemonic = "BLD"
      else :
        self.operation_mnemonic = "BILD"
    elif self.matchInstructionFormat("78") :
      self.operation_mnemonic = "MOV"
    elif self.matchInstructionFormat("7b") :
      self.operation_mnemonic = "EEPMOV"
    elif self.matchInstructionFormat("8*") :
      self.operation_mnemonic = "ADD"
    elif self.matchInstructionFormat("9*") :
      self.operation_mnemonic = "ADDX"
    elif self.matchInstructionFormat("a*") :
      self.operation_mnemonic = "CMP"
    elif self.matchInstructionFormat("b*") :
      self.operation_mnemonic = "SUBX"
    elif self.matchInstructionFormat("c*") :
      self.operation_mnemonic = "OR"
    elif self.matchInstructionFormat("d*") :
      self.operation_mnemonic = "XOR"
    elif self.matchInstructionFormat("e*") :
      self.operation_mnemonic = "AND"
    elif self.matchInstructionFormat("f*") :
      self.operation_mnemonic = "MOV"
    elif self.matchInstructionFormat("010") :
      self.operation_mnemonic = "MOV"
    elif self.matchInstructionFormat("014") :
      self.operation_mnemonic = "LDC/STC"
    elif self.matchInstructionFormat("018") :
      self.operation_mnemonic = "SLEEP"
    elif self.matchInstructionFormat("0a1") :
      self.operation_mnemonic = "INC"
    elif self.matchInstructionFormat("0a[1***]") :
      self.operation_mnemonic = "ADD"
    elif self.matchInstructionFormat("0b0") :
      self.operation_mnemonic = "ADDS"
    elif self.matchInstructionFormat("0b5") :
      self.operation_mnemonic = "INC"
    elif self.matchInstructionFormat("0b7") :
      self.operation_mnemonic = "INC"
    elif self.matchInstructionFormat("0b8") :
      self.operation_mnemonic = "ADDS"
    elif self.matchInstructionFormat("0b9") :
      self.operation_mnemonic = "ADDS"
    elif self.matchInstructionFormat("0bd") :
      self.operation_mnemonic = "INC"
    elif self.matchInstructionFormat("0bf") :
      self.operation_mnemonic = "INC"
    elif self.matchInstructionFormat("0f0") :
      self.operation_mnemonic = "DAA"
    elif self.matchInstructionFormat("0f[1***]") :
      self.operation_mnemonic = "MOV"
    elif self.matchInstructionFormat("100") :
      self.operation_mnemonic = "SHLL"
    elif self.matchInstructionFormat("101") :
      self.operation_mnemonic = "SHLL"
    elif self.matchInstructionFormat("103") :
      self.operation_mnemonic = "SHLL"
    elif self.matchInstructionFormat("108") :
      self.operation_mnemonic = "SHAL"
    elif self.matchInstructionFormat("109") :
      self.operation_mnemonic = "SHAL"
    elif self.matchInstructionFormat("10b") :
      self.operation_mnemonic = "SHAL"
    elif self.matchInstructionFormat("110") :
      self.operation_mnemonic = "SHLR"
    elif self.matchInstructionFormat("111") :
      self.operation_mnemonic = "SHLR"
    elif self.matchInstructionFormat("113") :
      self.operation_mnemonic = "SHLR"
    elif self.matchInstructionFormat("118") :
      self.operation_mnemonic = "SHAR"
    elif self.matchInstructionFormat("119") :
      self.operation_mnemonic = "SHAR"
    elif self.matchInstructionFormat("11b") :
      self.operation_mnemonic = "SHAR"
    elif self.matchInstructionFormat("120") :
      self.operation_mnemonic = "ROTXL"
    elif self.matchInstructionFormat("121") :
      self.operation_mnemonic = "ROTXL"
    elif self.matchInstructionFormat("123") :
      self.operation_mnemonic = "ROTXL"
    elif self.matchInstructionFormat("128") :
      self.operation_mnemonic = "ROTL"
    elif self.matchInstructionFormat("129") :
      self.operation_mnemonic = "ROTL"
    elif self.matchInstructionFormat("12b") :
      self.operation_mnemonic = "ROTL"
    elif self.matchInstructionFormat("130") :
      self.operation_mnemonic = "ROTXR"
    elif self.matchInstructionFormat("131") :
      self.operation_mnemonic = "ROTXR"
    elif self.matchInstructionFormat("133") :
      self.operation_mnemonic = "ROTXR"
    elif self.matchInstructionFormat("138") :
      self.operation_mnemonic = "ROTR"
    elif self.matchInstructionFormat("139") :
      self.operation_mnemonic = "ROTR"
    elif self.matchInstructionFormat("13b") :
      self.operation_mnemonic = "ROTR"
    elif self.matchInstructionFormat("170") :
      self.operation_mnemonic = "NOT"
    elif self.matchInstructionFormat("171") :
      self.operation_mnemonic = "NOT"
    elif self.matchInstructionFormat("173") :
      self.operation_mnemonic = "NOT"
    elif self.matchInstructionFormat("175") :
      self.operation_mnemonic = "EXTU"
    elif self.matchInstructionFormat("177") :
      self.operation_mnemonic = "EXTU"
    elif self.matchInstructionFormat("178") :
      self.operation_mnemonic = "ENG"
    elif self.matchInstructionFormat("179") :
      self.operation_mnemonic = "ENG"
    elif self.matchInstructionFormat("17a") :
      self.operation_mnemonic = "ENG"
    elif self.matchInstructionFormat("17e") :
      self.operation_mnemonic = "EXTS"
    elif self.matchInstructionFormat("17f") :
      self.operation_mnemonic = "EXTS"
    elif self.matchInstructionFormat("1a0") :
      self.operation_mnemonic = "DEC"
    elif self.matchInstructionFormat("1a[1***]") :
      self.operation_mnemonic = "SUB"
    elif self.matchInstructionFormat("1b0") :
      self.operation_mnemonic = "SUBS"
    elif self.matchInstructionFormat("1b5") :
      self.operation_mnemonic = "DEC"
    elif self.matchInstructionFormat("1b7") :
      self.operation_mnemonic = "DEC"
    elif self.matchInstructionFormat("1b8") :
      self.operation_mnemonic = "SUBS"
    elif self.matchInstructionFormat("1b9") :
      self.operation_mnemonic = "SUBS"
    elif self.matchInstructionFormat("1bd") :
      self.operation_mnemonic = "DEC"
    elif self.matchInstructionFormat("1bf") :
      self.operation_mnemonic = "DEC"
    elif self.matchInstructionFormat("1f0") :
      self.operation_mnemonic = "DAS"
    elif self.matchInstructionFormat("1f[1***]") :
      self.operation_mnemonic = "CMP"
    elif self.matchInstructionFormat("580") :
      self.operation_mnemonic = "BRA"
    elif self.matchInstructionFormat("581") :
      self.operation_mnemonic = "BRN"
    elif self.matchInstructionFormat("582") :
      self.operation_mnemonic = "BHI"
    elif self.matchInstructionFormat("583") :
      self.operation_mnemonic = "BLS"
    elif self.matchInstructionFormat("584") :
      self.operation_mnemonic = "BCC"
    elif self.matchInstructionFormat("585") :
      self.operation_mnemonic = "BCS"
    elif self.matchInstructionFormat("586") :
      self.operation_mnemonic = "BNE"
    elif self.matchInstructionFormat("587") :
      self.operation_mnemonic = "BEQ"
    elif self.matchInstructionFormat("588") :
      self.operation_mnemonic = "BVC"
    elif self.matchInstructionFormat("589") :
      self.operation_mnemonic = "BVS"
    elif self.matchInstructionFormat("58a") :
      self.operation_mnemonic = "BPL"
    elif self.matchInstructionFormat("58b") :
      self.operation_mnemonic = "BMI"
    elif self.matchInstructionFormat("58c") :
      self.operation_mnemonic = "BGE"
    elif self.matchInstructionFormat("58d") :
      self.operation_mnemonic = "BLT"
    elif self.matchInstructionFormat("58e") :
      self.operation_mnemonic = "BGT"
    elif self.matchInstructionFormat("58f") :
      self.operation_mnemonic = "BLE"
    elif self.matchInstructionFormat("790") :
      self.operation_mnemonic = "MOV"
    elif self.matchInstructionFormat("791") :
      self.operation_mnemonic = "ADD"
    elif self.matchInstructionFormat("792") :
      self.operation_mnemonic = "CMP"
    elif self.matchInstructionFormat("793") :
      self.operation_mnemonic = "SUB"
    elif self.matchInstructionFormat("794") :
      self.operation_mnemonic = "OR"
    elif self.matchInstructionFormat("795") :
      self.operation_mnemonic = "XOR"
    elif self.matchInstructionFormat("796") :
      self.operation_mnemonic = "AND"
    elif self.matchInstructionFormat("7a0") :
      self.operation_mnemonic = "MOV"
    elif self.matchInstructionFormat("7a1") :
      self.operation_mnemonic = "ADD"
    elif self.matchInstructionFormat("7a2") :
      self.operation_mnemonic = "CMP"
    elif self.matchInstructionFormat("7a3") :
      self.operation_mnemonic = "SUB"
    elif self.matchInstructionFormat("7a4") :
      self.operation_mnemonic = "OR"
    elif self.matchInstructionFormat("7a5") :
      self.operation_mnemonic = "XOR"
    elif self.matchInstructionFormat("7a6") :
      self.operation_mnemonic = "AND"
    elif self.matchInstructionFormat("01c050") :
      self.operation_mnemonic = "MULXS"
    elif self.matchInstructionFormat("01c052") :
      self.operation_mnemonic = "MULXS"
    elif self.matchInstructionFormat("01d051") :
      self.operation_mnemonic = "DIVXS"
    elif self.matchInstructionFormat("01d053") :
      self.operation_mnemonic = "DIVXS"
    elif self.matchInstructionFormat("01f064") :
      self.operation_mnemonic = "OR"
    elif self.matchInstructionFormat("01f065") :
      self.operation_mnemonic = "XOR"
    elif self.matchInstructionFormat("01f066") :
      self.operation_mnemonic = "AND"
    elif self.matchInstructionFormat("7c*063") :
      self.operation_mnemonic = "BTST"
    elif self.matchInstructionFormat("7c*073") :
      self.operation_mnemonic = "BTST"
    elif self.matchInstructionFormat("7c*073") :
      if self.matchInstructionFormat("******[0***]") :
        self.operation_mnemonic = "BOR"
      else :
        self.operation_mnemonic = "BIOR"
    elif self.matchInstructionFormat("7c*073") :
      if self.matchInstructionFormat("******[0***]") :
        self.operation_mnemonic = "BXOR"
      else :
        self.operation_mnemonic = "BIXOR"
    elif self.matchInstructionFormat("7c*073") :
      if self.matchInstructionFormat("******[0***]") :
        self.operation_mnemonic = "BAND"
      else :
        self.operation_mnemonic = "BIAND"
    elif self.matchInstructionFormat("7c*073") :
      if self.matchInstructionFormat("******[0***]") :
        self.operation_mnemonic = "BLD"
      else :
        self.operation_mnemonic = "BILD"
    elif self.matchInstructionFormat("7d*060") :
      self.operation_mnemonic = "BSET"
    elif self.matchInstructionFormat("7d*061") :
      self.operation_mnemonic = "BNOT"
    elif self.matchInstructionFormat("7d*062") :
      self.operation_mnemonic = "BCLR"
    elif self.matchInstructionFormat("7d*067") :
      if self.matchInstructionFormat("******[0***]") :
        self.operation_mnemonic = "BST"
      else :
        self.operation_mnemonic = "BIST"
    elif self.matchInstructionFormat("7d*070") :
      self.operation_mnemonic = "BSET"
    elif self.matchInstructionFormat("7d*071") :
      self.operation_mnemonic = "BNOT"
    elif self.matchInstructionFormat("7d*072") :
      self.operation_mnemonic = "BCLR"
    elif self.matchInstructionFormat("7e**63") :
      self.operation_mnemonic = "BTST"
    elif self.matchInstructionFormat("7e**64") :
      if self.matchInstructionFormat("******[0***]") :
        self.operation_mnemonic = "BOR"
      else :
        self.operation_mnemonic = "BIOR"
    elif self.matchInstructionFormat("7e**65") :
      if self.matchInstructionFormat("******[0***]") :
        self.operation_mnemonic = "BXOR"
      else :
        self.operation_mnemonic = "BIXOR"
    elif self.matchInstructionFormat("7e**66") :
      if self.matchInstructionFormat("******[0***]") :
        self.operation_mnemonic = "BAND"
      else :
        self.operation_mnemonic = "BIAND"
    elif self.matchInstructionFormat("7e**67") :
      if self.matchInstructionFormat("******[0***]") :
        self.operation_mnemonic = "BLD"
      else :
        self.operation_mnemonic = "BLID"
    elif self.matchInstructionFormat("7f**60") :
      self.operation_mnemonic = "BSET"
    elif self.matchInstructionFormat("7f**61") :
      self.operation_mnemonic = "BNOT"
    elif self.matchInstructionFormat("7f**62") :
      self.operation_mnemonic = "BCLR"
    elif self.matchInstructionFormat("7f**67") :
      if self.matchInstructionFormat("******[0***]") :
        self.operation_mnemonic = "BST"
      else :
        self.operation_mnemonic = "BIST"
    elif self.matchInstructionFormat("7f**70") :
      self.operation_mnemonic = "BSET"
    elif self.matchInstructionFormat("7f**71") :
      self.operation_mnemonic = "BNOT"
    elif self.matchInstructionFormat("7f**72") :
      self.operation_mnemonic = "BCLR"

  def calcEffectiveAddress(self, operand):
    if operand['addressing'] == None :
      pass

    elif operand['addressing'] == "immidiate" :
      operand['mnemonic'] = "#0x%x" % operand['value']

    elif operand['addressing'] == "impliedImmidiate" :
      operand['mnemonic'] = "#%x" % operand['value']

    elif operand['addressing'] == "register" :
      if self.operand_size == "L" :
        operand['mnemonic'] = "er%x" % operand['value']
      elif self.operand_size == "W" :
        if (operand['value']>>3)&1 :
          operand['mnemonic'] = "e%x" % (operand['value']&0x07)
        else :
          operand['mnemonic'] = "r%x" % (operand['value']&0x07)
      elif self.operand_size == "B" :
        if (operand['value']>>3)&1 :
          operand['mnemonic'] = "r%xl" % (operand['value']&0x07)
        else :
          operand['mnemonic'] = "r%xh" % (operand['value']&0x07)

    elif operand['addressing'] == "registerIndirect" :
      operand['effective_address'] = self.regulerRegisters[operand['value']]
      operand['mnemonic'] = "@er%x" % operand['value']

    elif operand['addressing'] == "registerIndirectDisplacement16" :
      if (operand['disp'] >> 15) & 1 :
        disp = operand['disp'] - (1<<16)
      else :
        disp = operand['disp']
      operand['effective_address'] = self.regulerRegisters[operand['value']] + disp
      operand['mnemonic'] = "@(0x%x:16,er%x)" % (operand['disp'], operand['value'])

    elif operand['addressing'] == "registerIndirectDisplacement24" :
      if (operand['disp'] >> 23) & 1 :
        disp = operand['disp'] - (1<<24)
      else :
        disp = operand['disp']
      operand['effective_address'] = self.regulerRegisters[operand['value']] + disp
      operand['mnemonic'] = "@(0x%x:24,er%x)" % (operand['disp'], operand['value'])

    elif operand['addressing'] == "registerIndirectIncrement" :
      operand['effective_address'] = self.get32bitRegistor(operand['value'])
      if self.operand_size == "B" :
        self.add32bitRegistor(operand['value'], 1)
      elif self.operand_size == "W" :
        self.add32bitRegistor(operand['value'], 2)
      elif self.operand_size == "L" :
        self.add32bitRegistor(operand['value'], 4)
      operand['mnemonic'] = "@er%x+" % operand['value']

    elif operand['addressing'] == "registerindirectDecrement" :
      if self.operand_size == "B" :
        self.add32bitRegistor(operand['value'], -1)
      elif self.operand_size == "W" :
        self.add32bitRegistor(operand['value'], -2)
      elif self.operand_size == "L" :
        self.add32bitRegistor(operand['value'], -4)
      operand['effective_address'] = self.get32bitRegistor(operand['value'])

      operand['mnemonic'] = "@-er%x" % operand['value']

    elif operand['addressing'] == "absolute8" :
      operand['effective_address'] = 0xffff00 + operand['value']
      operand['mnemonic'] = "@0x%x:8" % operand['value']

    elif operand['addressing'] == "absolute16" :
      if (operand['value'] >> 15) & 1 :
        operand['effective_address'] =  operand['value'] - (1<<16)
      else :
        operand['effective_address'] = operand['value']
      operand['mnemonic'] = "@0x%x:16" % operand['value']

    elif operand['addressing'] == "absolute24" :
      operand['effective_address'] = operand['value']
      operand['mnemonic'] = "@0x%x:24" % operand['value']

    elif operand['addressing'] == "pcRelative8" :
      if (operand['disp'] >> 7) & 1 :
        disp = operand['disp'] - (1<<8)
      else :
        disp = operand['disp']
      operand['effective_address'] = self.programCounter+disp
      operand['mnemonic'] = ".%+d (0x%x)" % (disp,
                                             operand['effective_address'])

    elif operand['addressing'] == "pcRelative16" :
      if (operand['disp'] >> 15) & 1 :
        disp = operand['disp'] - (1<<16)
      else :
        disp = operand['disp']
      operand['effective_address'] = self.programCounter+disp
      operand['mnemonic'] = ".%+d (0x%x)" % (disp,
                                             operand['effective_address'])

    elif operand['addressing'] == "memoryIndirect" :
      operand['effective_address'] = self.memory[operand['value']]
      operand['mnemonic'] = "@@%x" % operand['value']

    operand['effective_address'] &= 0xffffff
  
  def changeNFlag(self) :
    if self.operand_size == "L" :
      self.conditionCodeN = ((self.result>>31)&1 == 1)
    elif self.operand_size == "W" :
      self.conditionCodeN = ((self.result>>15)&1 == 1)
    elif self.operand_size == "B" :
      self.conditionCodeN = ((self.result>>7)&1 == 1)
    
  def changeZFlag(self) :
    if self.operand_size == "L" :
      self.conditionCodeZ = ((self.result & 0xffffffff) == 0)
    elif self.operand_size == "W" :
      self.conditionCodeZ = ((self.result & 0xffff) == 0)
    elif self.operand_size == "B" :
      self.conditionCodeZ = ((self.result & 0xff) == 0)

  def changeVFlag(self, left, right) :
    if self.operand_size == "L" :
      if ((((right>>31)&1) == ((left>>31)&1)) and
          (((right>>31)&1) != ((self.result>>31)&1))):
        self.conditionCodeV = True
      else :
        self.conditionCodeV = False
    elif self.operand_size == "W" :
      if ((((right>>15)&1) == ((left>>15)&1)) and
          (((right>>15)&1) != ((self.result>>15)&1))):
        self.conditionCodeV = True
      else :
        self.conditionCodeV = False
    elif self.operand_size == "B" :
      if ((((right>>7)&1) == ((left>>7)&1)) and
          (((right>>7)&1) != ((self.result>>7)&1))):
        self.conditionCodeV = True
      else :
        self.conditionCodeV = False

  def changeCFlag(self) :
    if self.operand_size == "L" :
      self.conditionCodeC = ((self.result>>32)&1 == 1)
    elif self.operand_size == "W" :
      self.conditionCodeC = ((self.result>>16)&1 == 1)
    elif self.operand_size == "B" :
      self.conditionCodeC = ((self.result>>8)&1 == 1)

  def translateNegative(self, value) :
    if self.operand_size == "L" :
      return (-value)&0xffffffff
    elif self.operand_size == "W" :
      return (-value)&0xffff
    elif self.operand_size == "B" :
      return (-value)&0xff

  def processOperation(self) :
    if self.operation_mnemonic == "ADD" :
      self.right_side_value = self.getSource()
      self.left_side_value = self.getDestination()
      self.result = self.left_side_value + self.right_side_value
      self.setDestination(self.result)

      self.changeNFlag()
      self.changeZFlag()
      self.changeVFlag(self.left_side_value, self.right_side_value)
      self.changeCFlag()

    elif self.operation_mnemonic == "ADDS" :
      self.right_side_value = self.getSource()
      self.left_side_value = self.getDestination()
      self.result = self.left_side_value + self.right_side_value
      self.setDestination(self.result)

    elif self.operation_mnemonic == "ADDX" :
      self.right_side_value = self.getSource()
      self.left_side_value = self.getDestination()
      self.result = (self.left_side_value
                     +self.right_side_value
                     +int(self.conditionCodeC))
      self.setDestination(self.result)

      self.changeNFlag()
      self.changeZFlag()
      self.changeVFlag(self.left_side_value, self.right_side_value)
      if self.conditionCodeV == False :
        self.changeVFlag(self.left_side_value+self.right_side_value,
                         int(self.conditionCodeC))
      self.changeCFlag()
      
    elif self.operation_mnemonic == "AND" :
      self.right_side_value = self.getSource()
      self.left_side_value = self.getDestination()
      self.result = self.left_side_value & self.right_side_value
      self.setDestination(self.result)

      self.changeNFlag()
      self.changeZFlag()
      self.conditionCodeV = False
      
    elif self.operation_mnemonic == "ANDC" :
      self.right_side_value = self.getSource()
      self.left_side_value = self.getConditionCode()
      self.result = self.left_side_value & self.right_side_value
      self.setConditionCode(self.result)

    elif self.operation_mnemonic == "BAND" :
      self.right_side_value = bool((self.getDestination()>>self.getSource())&1)
      self.left_side_value = self.conditionCodeC
      self.result = self.right_side_value and self.left_side_value
      conditionCodeC = self.result

    elif self.operation_mnemonic == "BRA" :
      self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BRN" :
      pass
    elif self.operation_mnemonic == "BHI" :
      if (self.conditionCodeC or self.conditionCodeH) == False :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BLS" :
      if (self.conditionCodeC or self.conditionCodeH) == True :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BCC" :
      if self.conditionCodeC == False :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BCS" :
      if self.conditionCodeC == True :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BNE" :
      if self.conditionCodeZ == False :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BEQ" :
      if self.conditionCodeZ == True :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BVC" :
      if self.conditionCodeV == False :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BVS" :
      if self.conditionCodeV == True :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BPL" :
      if self.conditionCodeN == False :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BMI" :
      if self.conditionCodeN == True :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BGE" :
      if myExor(self.conditionCodeN, self.conditionCodeV) == True  :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BLT" :
      if myExor(self.conditionCodeN, self.conditionCodeV) == False :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BGT" :
      if (self.conditionCodeZ or myExor(self.conditionCodeN, self.conditionCodeV)) == False :
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BLE" :
      if (self.conditionCodeZ or myExor(self.conditionCodeN, self.conditionCodeV)) == True:
        self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BCLR" :
      pass
    elif self.operation_mnemonic == "BIAND" :
      pass
    elif self.operation_mnemonic == "BILD" :
      pass
    elif self.operation_mnemonic == "BIOR" :
      pass
    elif self.operation_mnemonic == "BIST" :
      pass
    elif self.operation_mnemonic == "BIXOR" :
      pass
    elif self.operation_mnemonic == "BILD" :
      pass
    elif self.operation_mnemonic == "BNOT" :
      pass
    elif self.operation_mnemonic == "BOR" :
      pass
    elif self.operation_mnemonic == "BSET" :
      pass
    elif self.operation_mnemonic == "BSR" :
      self.pushStack(self.getProgramCounter())
      self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "BST" :
      pass
    elif self.operation_mnemonic == "BTST" :
      pass
    elif self.operation_mnemonic == "BXOR" :
      pass
    elif self.operation_mnemonic == "CMP" :
      self.right_side_value = self.getSource()
      self.left_side_value = self.getDestination()
      self.result = self.left_side_value + self.translateNegative(self.right_side_value)
      
      self.changeNFlag()
      self.changeZFlag()
      self.changeVFlag(self.left_side_value, self.translateNegative(self.right_side_value))
      self.changeCFlag()

    elif self.operation_mnemonic == "DAA" :
      pass
    elif self.operation_mnemonic == "DAS" :
      pass
    elif self.operation_mnemonic == "DEC" :
      pass
    elif self.operation_mnemonic == "DIVXS" :
      pass
    elif self.operation_mnemonic == "EEPMOV" :
      pass
    elif self.operation_mnemonic == "EXTS" :
      pass
    elif self.operation_mnemonic == "EXTU" :
      pass
    elif self.operation_mnemonic == "INC" :
      pass
    elif self.operation_mnemonic == "JMP" :
      pass
    elif self.operation_mnemonic == "JSR" :
      self.pushStack(self.getProgramCounter())
      self.setProgramCounter(self.operands['src']['effective_address'])
    elif self.operation_mnemonic == "LDC" :
      pass
    elif self.operation_mnemonic == "MOV" :
      self.left_side_value = self.getSource()
      self.result = self.left_side_value
      self.setDestination(self.result)

      self.changeNFlag()
      self.changeZFlag()

    elif self.operation_mnemonic == "MOVFPE" :
      pass
    elif self.operation_mnemonic == "MOVTPE" :
      pass
    elif self.operation_mnemonic == "MULXS" :
      pass
    elif self.operation_mnemonic == "MULXU" :
      pass
    elif self.operation_mnemonic == "NEG" :
      pass
    elif self.operation_mnemonic == "NOP" :
      pass
    elif self.operation_mnemonic == "NOT" :
      pass
    elif self.operation_mnemonic == "OR" :
      pass
    elif self.operation_mnemonic == "ORC" :
      pass
    elif self.operation_mnemonic == "POP" :
      pass
    elif self.operation_mnemonic == "PUSH" :
      pass
    elif self.operation_mnemonic == "ROTL" :
      pass
    elif self.operation_mnemonic == "ROTR" :
      pass
    elif self.operation_mnemonic == "ROTXL" :
      pass
    elif self.operation_mnemonic == "ROTXR" :
      pass
    elif self.operation_mnemonic == "RTE" :
      pass
    elif self.operation_mnemonic == "RTS" :
      self.setProgramCounter(self.popStack())
    elif self.operation_mnemonic == "SHAL" :
      pass
    elif self.operation_mnemonic == "SHAR" :
      pass
    elif self.operation_mnemonic == "SHLL" :
      pass
    elif self.operation_mnemonic == "SHLR" :
      pass
    elif self.operation_mnemonic == "SLEEP" :
      self.state = "sleep"
    elif self.operation_mnemonic == "STC" :
      pass
    elif self.operation_mnemonic == "SUB" :
      self.right_side_value = self.getSource()
      self.left_side_value = self.getDestination()
      self.result = (self.left_side_value
                     +self.translateNegative(self.right_side_value))
      self.setDestination(self.result)
        
      self.changeNFlag()
      self.changeZFlag()
      self.changeVFlag(self.left_side_value,
                       self.translateNegative(self.right_side_value))
      self.changeCFlag()

    elif self.operation_mnemonic == "SUBS" :
      self.right_side_value = self.getSource()
      self.left_side_value = self.getDestination()
      self.result = (self.left_side_value
                     +self.translateNegative(self.right_side_value))
      self.setDestination(self.result)
    elif self.operation_mnemonic == "SUBX" :
      pass
    elif self.operation_mnemonic == "TRAPA" :
      pass
    elif self.operation_mnemonic == "XOR" :
      pass
    elif self.operation_mnemonic == "XOR" :
      pass
    elif self.operation_mnemonic == "XOR" :
      pass
    elif self.operation_mnemonic == "XORC" :
      pass

  def runStep(self) :
    self.decodeOpecode()

    self.disasm = ("%x: "%self.programCounter)
    for x in range(self.opecode_size) :
      self.disasm += "%02x " % self.memory[self.programCounter+x]
    for x in range(26-len(self.disasm )) :
      self.disasm += " "

    self.addToProgramCounter(self.opecode_size)
    self.calcEffectiveAddress(self.operands['src'])
    self.calcEffectiveAddress(self.operands['dst'])
    self.processOperation()

    self.disasm += self.getMnemonic()

  def matchInstructionFormat(self, fmt) :
    bit_index = 0
    
    bit_mode = False
    for ch in fmt :
      if ch == ']' :
        bit_mode = False
      elif ch == '[' :
        bit_mode = True
      elif bit_mode == False :
        value = self.memory[self.programCounter+bit_index/8]>>(4*(1-bit_index/4%2)) & 0x0f
        if ch != '*' and int(ch, 16) != value :
          return False
        bit_index += 4
      else :
        value = self.memory[self.programCounter+bit_index/8]>>(7-bit_index%8) & 0x01
        if ch != '*' and int(ch, 10) != value :
          return False
        bit_index += 1

    self.format_size = bit_index/8
    return True

def myExor(a, b) :
  return a!=b
