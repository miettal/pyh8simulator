/* 
  H8300Hシミュレータ用リンカスクリプト（元ファイルから余計な分を削ったもの）
*/

/* ファイル書式 */
OUTPUT_FORMAT("coff-h8300")
/* ターゲットアーキテクチャ */
OUTPUT_ARCH(h8300h)

/* Memory Map
 +--------+-------+--------------+
 |address |rom/ram|section(etc..)|
 +--------+-------+--------------+
 |0x400000| rom   |.text         |
 |        |       |.rodata       |
 |        |       |.tors         |
 |        |       |.vectors      |
 +--------+-------+--------------+
 |0x500000| ram   |.data         |
 |        |       |.bss          |
 |0x600000|       |stack         |
 +--------+-------+--------------+
 */

/* _startルーチンをエントリポイントに設定 */
ENTRY("_start")

/* 初期スタックポインタの設定 */
PROVIDE(_stack = 0x600000);

MEMORY
{
  rom : o = 0x400000,
        l = 0x100000
  ram : o = 0x500000,
        l = 0x100000
}
SECTIONS
{
  .text    :{} > rom
  .rodata  :{} > rom
  .tors    :{} > rom
  .vectors :{} > rom
  .data    :{} > ram
  .bss     :{} > ram
}
