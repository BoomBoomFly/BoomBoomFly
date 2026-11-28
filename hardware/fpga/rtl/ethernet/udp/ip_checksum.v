// ==================== eth_udp_checksums.v ====================
/////////////////////////////////////////////////////////////////////////////////
// Company       : 武汉芯路恒科技有限公司
//                 http://xiaomeige.taobao.com
// Web           : http://www.corecourse.cn
//
// Create Date   : 2019/05/01 00:00:00
// Module Name   : ip_checksum
// Description   : ip头部校验模块
//
// Dependencies  :
//
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
//
/////////////////////////////////////////////////////////////////////////////////

module ip_checksum(
  input           clk            ,
  input           reset_p        ,

  input           cal_en         ,

  input   [3:0]   IP_ver         ,
  input   [3:0]   IP_hdr_len     ,
  input   [7:0]   IP_tos         ,
  input   [15:0]  IP_total_len   ,
  input   [15:0]  IP_id          ,
  input           IP_rsv         ,
  input           IP_df          ,
  input           IP_mf          ,
  input   [12:0]  IP_frag_offset ,
  input   [7:0]   IP_ttl         ,
  input   [7:0]   IP_protocol    ,
  input   [31:0]  src_ip         ,
  input   [31:0]  dst_ip         ,

  output  [15:0]  checksum         ,
  output reg      cal_done_o
);

  reg  [16:0]sum01_q, sum23_q, sum45_q, sum67_q;
  reg  [15:0]dst_ip_low_q;
  reg  pair_valid_q, suma_valid_q, sumb_valid_q;
  reg  [19:0]suma;
  reg  [16:0]sumb;
  reg  [15:0]checksum_q;

  // 九个16位首部字按树形分组相加，避免长串行加法器。
  wire [15:0] word0 = {IP_ver,IP_hdr_len,IP_tos};
  wire [15:0] word3 = {IP_rsv,IP_df,IP_mf,IP_frag_offset};
  wire [15:0] word4 = {IP_ttl,IP_protocol};
  wire [16:0] sum01 = {1'b0,word0} + {1'b0,IP_total_len};
  wire [16:0] sum23 = {1'b0,IP_id} + {1'b0,word3};
  wire [16:0] sum45 = {1'b0,word4} + {1'b0,src_ip[31:16]};
  wire [16:0] sum67 = {1'b0,src_ip[15:0]} + {1'b0,dst_ip[31:16]};
  wire [17:0] sum0123 = {1'b0,sum01_q} + {1'b0,sum23_q};
  wire [17:0] sum4567 = {1'b0,sum45_q} + {1'b0,sum67_q};
  wire [18:0] sum01234567 = {1'b0,sum0123} + {1'b0,sum4567};
  wire [19:0] suma_next = {1'b0,sum01234567} + {4'd0,dst_ip_low_q};

  always@(posedge clk or posedge reset_p)
  if(reset_p) begin
    sum01_q<=17'd0;sum23_q<=17'd0;sum45_q<=17'd0;sum67_q<=17'd0;
    dst_ip_low_q<=16'd0;
    pair_valid_q<=1'b0;suma_valid_q<=1'b0;sumb_valid_q<=1'b0;cal_done_o<=1'b0;
    suma<=20'd0;sumb<=17'd0;checksum_q<=16'd0;
  end else begin
    // 先寄存四组首部字对和有效脉冲，把总长度输入与后续折叠树隔开一拍。
    pair_valid_q<=cal_en;
    if(cal_en) begin
      sum01_q<=sum01;sum23_q<=sum23;sum45_q<=sum45;sum67_q<=sum67;
      dst_ip_low_q<=dst_ip[15:0];
    end
    suma_valid_q<=pair_valid_q;
    if(pair_valid_q)suma<=suma_next;
    sumb_valid_q<=suma_valid_q;
    if(suma_valid_q)sumb<={1'b0,suma[19:16]}+{1'b0,suma[15:0]};
    cal_done_o<=sumb_valid_q;
    if(sumb_valid_q)checksum_q<=~(sumb[15:0]+{15'd0,sumb[16]});
  end

  assign checksum = checksum_q;

endmodule
