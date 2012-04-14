#define OUTPUT (*(unsigned char*)0x100002)

void putchar(unsigned char c)
{
  OUTPUT = c;
}

void putstr(unsigned char *s)
{
  int i;

  for(i=0;s[i];i++) {
    putchar(s[i]);
  }
}

void puts(unsigned char *s)
{
  putstr(s);
  putchar('\n');
}

int main(void)
{
  puts("Hello, World!");

  return 0;
}

