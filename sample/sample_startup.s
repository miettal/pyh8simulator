/* 
  H8300Hシミュレータ用スタートアップルーチン（元ファイルから余計な分を削ったもの）
*/

/* h8300hアセンブリ */
	.h8300h
/* textセクション */
	.section .text
/* _start をグローバル宣言 */
	.global _start

_start:
/* スタックポインタをセット */
	mov.l   #0x600000, er7
/* Cのmain関数呼び出し */
_loop:
	jsr     @_main
/* ループ先頭に戻る */
	bra     _loop
