# -*- coding: utf-8 -*-
import h8simulator

class SFormat() :
  def __init__(self, filename=None) :
    # プログラム名
    self.programName = ""
    # エントリアドレス
    self.entryAddress = 0
    # メモリデータ
    self.memoryData = {}
    
    if filename :
      self.loadFromString(filename)

  def setProgramName(self, value) :
    self.programName = value

  def getProgramName(self) :
    return self.programName

  def setEntryAddress(self, value) :
    self.entryAddress = value

  def getEntryAddress(self) :
    return self.entryAddress
    
  def setMemoryData(self, address, data) :
    '''
        メモリにバイトデータをセットするメソッド
        address:開始アドレス
        data:バイトデータ（整数のリスト，要素は8ビットとみなした整数値）
    '''
    for byte in data :
      self.memoryData[address] = byte
      address += 1
      
  def getMemoryData(self) :
    return self.memoryData
    
  def loadFromFile(self, filename) :
    '''
        S-Format 解析用メソッド（引数がファイル名版）
        filename:Sフォーマットのファイル名またはファイルへのパス
    '''
    self.loadFromString(open(filename, 'r').read())
  
  def loadFromString(self, string) :
    '''
        S-Format 解析用メソッド
        string:Sフォーマットの文字列（open(filename,'r').read()などを直接渡せばいい）
    '''
    for line in string.split() :
      if line[:2] == "S0" : 
        self.setProgramName(''.join(map(chr, hexStrToNbyteList(line[8:-2], 1))))
      elif line[:2] == "S1" :
        address = hexStrToNbyteList(line[4:8], 2)[0]
        data = hexStrToNbyteList(line[8:-2], 1)
        self.setMemoryData(address, data)
      elif line[:2] == "S2" : 
        address = hexStrToNbyteList(line[4:10], 3)[0]
        data = hexStrToNbyteList(line[10:-2], 1)
        self.setMemoryData(address, data)
      elif line[:2] == "S3" : 
        address = hexStrToNbyteList(line[4:12], 4)[0]
        data = hexStrToNbyteList(line[12:-2], 1)
        self.setMemoryData(address, data)
      elif line[:2] == "S4" : 
        pass
      elif line[:2] == "S5" : 
        pass
      elif line[:2] == "S6" : 
        pass
      elif line[:2] == "S7" : 
        address = hexStrToNbyteList(line[4:12], 4)[0]
        self.setEntryAddress(address)
      elif line[:2] == "S8" : 
        address = hexStrToNbyteList(line[4:10], 3)[0]
        self.setEntryAddress(address)
      elif line[:2] == "S9" : 
        address = hexStrToNbyteList(line[4:8], 2)[0]
        self.setEntryAddress(address)
      else :
        raise Exception("invalid format")

def hexStrToNbyteList(s, n) :
    return [ int(s[2*n*x:2*n*(x+1)], 16) for x in range(len(s)/(2*n))]
    
class SimpleH8simulator(h8simulator.H8simulator) :
  def __init__(self) :
    h8simulator.H8simulator.__init__(self)
    
    # SFormatファイル
    self.sformat = SFormat()

    # IOアドレス
    self.outputAddress = 0x100002
    
  def load(self, filename) :
    self.sformat.loadFromFile(filename)
    
  def reset(self) :
    self.loadMemory(self.sformat.getMemoryData())
    self.setProgramCounter(self.sformat.getEntryAddress())
    for x in range(8) :
      self.set32bitRegistor(x, 0)
    self.setConditionCode(0)
    self.outputBuf = []
    self.set8bitMemory(self.outputAddress, 0)

  def runStep(self) :
    h8simulator.H8simulator.runStep(self)
    self.runIO()
    
  def runIO(self) :
    if self.get8bitMemory(self.outputAddress) != 0 :
      self.outputBuf.insert(0, "%c" % self.get8bitMemory(self.outputAddress))
      self.set8bitMemory(self.outputAddress, 0)

  def getDisAssembly(self, address=None, disasm={}) :
    if address == None :
      self.reset()
    else :
      self.setProgramCounter(address)
    jump_operation_list = [
      'BHI',
      'BLS',
      'BCC',
      'BCS',
      'BNE',
      'BEQ',
      'BVC',
      'BVS',
      'BPL',
      'BMI',
      'BGE',
      'BLT',
      'BGT',
      'BLE',
      'BSR',
      'JSR',
    ]
    while True :
      old_program_counter = self.getProgramCounter()

      try :
        self.runStep()
      except :
        pass
      
      disasm[old_program_counter] = self.getMnemonic()

      if self.operation_mnemonic == "RTS" :
        break
    
      if any([self.operation_mnemonic == x for x in jump_operation_list]) :
        jump1 = old_program_counter + self.opecode_size
        jump2 = self.operands['src']['effective_address']
        if jump1 not in disasm :
          self.getDisAssembly(jump1, disasm)
        if jump2 not in disasm :
          self.getDisAssembly(jump2, disasm)
        break

    return disasm
