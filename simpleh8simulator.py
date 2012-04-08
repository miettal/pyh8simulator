# -*- coding: utf-8 -*-
import h8simulator

class SimpleH8simulator(h8simulator.H8simulator) :
  def __init__(self) :
    h8simulator.H8simulator.__init__(self)

    # プログラム名
    self.programName = ""
    # エントリアドレス
    self.entryAddress = 0

    self.disasm_line = ""

    # IO周り初期化
    self.OutputBuf = []
    self.outputAddress = 0x100002
    self.set8bitMemory(self.outputAddress, 0);

  def loadSFormatFromFile(self, filename) :
    '''
        S-Format 解析用メソッド（引数がファイル名版）
        filename:Sフォーマットのファイル名またはファイルへのパス
    '''
    self.loadSFormatFromString(open(filename, 'r').read())
  
  def loadSFormatFromString(self, sformat_string) :
    '''
        S-Format 解析用メソッド
        sformat_string:Sフォーマットの文字列（open(filename,'r').read()などを直接渡せばいい）
    '''
    for line in sformat_string.split() :
      if line[:2] == "S0" : 
        self.setProgramName(''.join(map(chr, hexStrToNbyteList(line[8:-2], 1))))
      if line[:2] == "S1" :
        address = hexStrToNbyteList(line[4:8], 2)[0]
        data = hexStrToNbyteList(line[8:-2], 1)
        self.setMemoryData(address, data)
      if line[:2] == "S2" : 
        address = hexStrToNbyteList(line[4:10], 3)[0]
        data = hexStrToNbyteList(line[10:-2], 1)
        self.setMemoryData(address, data)
      if line[:2] == "S3" : 
        address = hexStrToNbyteList(line[4:12], 4)[0]
        data = hexStrToNbyteList(line[12:-2], 1)
        self.setMemoryData(address, data)
      if line[:2] == "S4" : 
        pass
      if line[:2] == "S5" : 
        pass
      if line[:2] == "S6" : 
        pass
      if line[:2] == "S7" : 
        address = hexStrToNbyteList(line[4:12], 4)[0]
        self.setEntryAddress(address)
      if line[:2] == "S8" : 
        address = hexStrToNbyteList(line[4:10], 3)[0]
        self.setEntryAddress(address)
      if line[:2] == "S9" : 
        address = hexStrToNbyteList(line[4:8], 2)[0]
        self.setEntryAddress(address)

  def setMemoryData(self, address, data) :
    '''
        メモリにバイトデータをセットするメソッド
        address:開始アドレス
        data:バイトデータ（整数のリスト，要素は8ビットとみなした整数値）
    '''
    for byte in data :
      self.memory[address] = byte
      address += 1

  def setEntryAddress(self, entry_address) :
    self.entryAddress = entry_address

  def getEntryAddress(self) :
    return self.entryAddress
  
  def setProgramName(self, program_name) :
    self.programName = program_name

  def loadEntryAddressToProgramCounter(self) :
    self.setProgramCounter(self.getEntryAddress())

  def runStep(self) :
    old_programcounter = self.getProgramCounter()
    h8simulator.H8simulator.runStep(self)

    self.disasm_line = ("%x: "%old_programcounter)
    for x in range(self.opecode_size) :
      self.disasm_line += "%02x " % self.memory[old_programcounter+x]
    for x in range(26-len(self.disasm_line)) :
      self.disasm_line += " "
    self.disasm_line += self.getMnemonic()

    self.runIO()
    
  def runIO(self) :
    if self.get8bitMemory(self.outputAddress) != 0 :
      self.OutputBuf.insert(0, "%c" % self.get8bitMemory(self.outputAddress))
      self.set8bitMemory(self.outputAddress, 0)

  def getDisAssembly(self, address=None, disasm={}) :
    if address == None :
      self.loadEntryAddressToProgramCounter()
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
      
      disasm[old_program_counter] = self.disasm_line

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
    

def hexStrToNbyteList(s, n) :
    return [ int(s[2*n*x:2*n*(x+1)], 16) for x in range(len(s)/(2*n))]
