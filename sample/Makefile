TARGET = sample.mot
SOURCE_C = sample.c

LDSCRIPT = sample.x
STARTUP = sample_startup.s
TARGET_COFF = $(TARGET:.mot=.coff)

CC = h8300-hms-gcc
LD = h8300-hms-ld
OBJCOPY = h8300-hms-objcopy

OUTPUT_FORMAT = -O srec

CFLAGS = -mh -mrelax -mint32 -Wall

LDFLAGS = -T $(LDSCRIPT) -nostartfiles

OBJ = $(STARTUP:.s=.o) $(SOURCE_C:.c=.o)

.SUFFIXES: .c .s .o 

$(TARGET) : $(TARGET_COFF)
	$(OBJCOPY) -v $(OUTPUT_FORMAT) $(TARGET_COFF) $(TARGET)

$(TARGET_COFF) : $(OBJ)
	$(CC) $(CFLAGS) $(LDFLAGS) $(OBJ) -o $(TARGET_COFF)

clean :
	rm -f *.o $(TARGET) $(TARGET_COFF)

.c.o:
	$(CC) -c $(CFLAGS) $<
.s.o:
	$(CC) -c $(CFLAGS) $<
