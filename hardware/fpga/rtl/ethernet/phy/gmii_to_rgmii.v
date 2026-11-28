// ==================== rgmii_io.v ====================
//////////////////////////////////////////////////////////////////////////////////
// Company: 武汉芯路恒科技有限公司
// Engineer: www.corecourse.cn
//
// Create Date: 2021/09/20 00:00:00
// Design Name:
// Module Name:
// Project Name:
// Target Devices: xc7z020clg400-2
// Tool Versions: Vivado 2018.3
// Description: gmii转rgmii
//
// Dependencies:
//
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
//
//////////////////////////////////////////////////////////////////////////////////
module gmii_to_rgmii(
  reset_n,

  gmii_tx_clk,
  gmii_txd,
  gmii_txen,
  gmii_txer,

  rgmii_tx_clk,
  rgmii_txd,
  rgmii_txen
);



  input        reset_n;

  input        gmii_tx_clk;
  input  [7:0] gmii_txd;
  input        gmii_txen;
  input        gmii_txer;

  output       rgmii_tx_clk;
  output [3:0] rgmii_txd;
  output       rgmii_txen;

  // ODDR 在同一上升沿采样 D0/D1；先将完整 GMII 字/控制寄存，
  // 两相都从同一快照取值，保证字节与 TX_CTL 配对且固定延迟一拍。
  // 误码位与使能一并寄存，维持 TX_CTL=EN / EN^ER 的配对关系。
  (* syn_preserve=1 *) reg [9:0] gmii_tx_stage_q;
  always @(posedge gmii_tx_clk or negedge reset_n) begin
    if (!reset_n) begin
      gmii_tx_stage_q <= 10'd0;
    end else begin
      gmii_tx_stage_q <= {gmii_txer,gmii_txen,gmii_txd};
    end
  end

  generate
    genvar i;
        for(i=0;i<4;i=i+1)
        begin : rgmii_data_lane
        ODDR    U_ODDR_dq1
                (.Q0(rgmii_txd[i]),
                 .Q1(),
                 .D0(gmii_tx_stage_q[i]),
                 .D1(gmii_tx_stage_q[i+4]),
                 .TX(1'b1),
                 .CLK(gmii_tx_clk)
                );
        end
  endgenerate

	ODDR    U_ODDR_en1
			(.Q0(rgmii_txen),
             .Q1(),

             .D0(gmii_tx_stage_q[8]),
             .D1(gmii_tx_stage_q[8]^gmii_tx_stage_q[9]),
             .TX(1'b1),

             .CLK(gmii_tx_clk)
			);

	ODDR    U_ODDR_clk1
			(.Q0(rgmii_tx_clk),
             .Q1(),

             .D0(1'b1),
             .D1(1'b0),
             .TX(1'b1),

             .CLK(gmii_tx_clk)
			);

endmodule
