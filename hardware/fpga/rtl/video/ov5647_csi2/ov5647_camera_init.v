// ==================== ov5647_camera_init.v ====================
/////////////////////////////////////////////////////////////////////////////////
// Company       : 武汉芯路恒科技有限公司
//                 http://xiaomeige.taobao.com
// Web           : http://www.corecourse.cn
//
// Create Date   : 2019/05/01 00:00:00
// Module Name   : ov5647_camera_init
// Description   : 摄像头初始化驱动模块，仅支持本板OV5647 CSI-2 RAW10
//
// Dependencies  :
//
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
//
/////////////////////////////////////////////////////////////////////////////////

module ov5647_camera_init #(
  parameter SYS_CLOCK       = 50_000_000,//系统时钟采用50MHz
  parameter SCL_CLOCK       = 400_000,   //SCL总线时钟采用400kHz
  parameter integer LP11_RESET_PROBE = 0 //仅隔离验证候选启用
)
(
  input      Clk,
  input      Rst_n,

  output reg Init_Done,
  output     camera_rst_n,
  output     camera_pwdn,

  output     i2c_sclk,
  inout      i2c_sdat,
  input      [1:0] lp_clk_state,
  output     dphy_rx_reset_n,
  output     [30:0] lp11_probe_status
);
  localparam DELAY_1ms_CNT  = 1_000_000/(1_000_000_000/SYS_CLOCK);
  localparam DELAY_21ms_CNT = 21_000_000/(1_000_000_000/SYS_CLOCK);
  localparam DELAY_5ms_CNT  = 5_000_000/(1_000_000_000/SYS_CLOCK);
  localparam integer LP11_PROBE_ACTIVE = LP11_RESET_PROBE;
  localparam integer LP11_QUIET_CYCLES = (SYS_CLOCK >= 1000) ? (SYS_CLOCK / 1000) : 1;

  localparam [3:0] PROBE_STOP       = 4'd0;
  localparam [3:0] PROBE_WAIT_LP11  = 4'd1;
  localparam [3:0] PROBE_HOLD_LP11  = 4'd2;
  localparam [3:0] PROBE_RUN        = 4'd3;
  localparam [3:0] PROBE_FAULT      = 4'd4;

  wire [15:0]addr;
  wire [15:0]table_addr;
  reg wrreg_req;
  wire [7:0]wrdata;
  wire [7:0]table_wrdata;
  wire [7:0]rddata;
  wire RW_Done;
  wire ack;
  reg [31:0] i2c_dly_cnt_max;

  reg [7:0]cnt;
  wire [23:0]lut;

  wire [7:0]lut_size;
  wire [7:0]device_id;
  wire addr_mode;
  reg [3:0] probe_state;
  reg [1:0] probe_stop_index;
  reg [31:0] probe_quiet_count;
  reg [7:0] probe_reset_release_count;
  reg probe_fault;
  reg probe_lp11_seen;
  reg [1:0] probe_lp_clk00_count;
  reg probe_rx_release_done;
  (* ASYNC_REG="TRUE" *) reg [1:0] lp_clk_meta;
  (* ASYNC_REG="TRUE" *) reg [1:0] lp_clk_sync;
  wire probe_stop_override = LP11_PROBE_ACTIVE && (cnt == 8'd82) &&
                             (probe_state == PROBE_STOP);

  assign addr = probe_stop_override ?
                ((probe_stop_index == 2'd0) ? 16'h4800 :
                 (probe_stop_index == 2'd1) ? 16'h4202 : 16'h300d) : table_addr;
  assign wrdata = probe_stop_override ?
                  ((probe_stop_index == 2'd0) ? 8'h25 :
                   (probe_stop_index == 2'd1) ? 8'h0f : 8'h01) : table_wrdata;
  assign dphy_rx_reset_n = LP11_PROBE_ACTIVE ?
                           ((probe_state == PROBE_RUN) &&
                            probe_rx_release_done && !probe_fault) : Rst_n;
  assign lp11_probe_status = {
    probe_state,
    (LP11_PROBE_ACTIVE ? lp_clk_sync : 2'b00),
    (LP11_PROBE_ACTIVE && (lp_clk_sync == 2'b11)),
    dphy_rx_reset_n,
    probe_reset_release_count,
    probe_fault,
    Init_Done,
    probe_stop_index,
    probe_quiet_count[10:0]
  };

  assign camera_pwdn = 0;

  // 本板固定使用 OV5647 CSI-2 RAW10 初始化表。
    assign device_id = 8'h6c;
    assign addr_mode = 1'b1;
    assign table_addr = lut[23:8];
    assign table_wrdata = lut[7:0];
    // OV5647 初始化表共 96 项，含 Linux 流启动阶段的控制寄存器。
    assign lut_size = 96;

    ov5647_init_table_raw10 ov5647_init_table_raw10_inst
    (
      .addr (cnt ),
      .clk  (Clk ),
      .q    (lut )
    );

  // ACK/NACK 由 camera_init 的现有 I2C 完成边界提供；探针状态机只在 ACK 后推进。
  // CEN 探针在 LUT 即将写 4800=04 时插入 Linux 停流三写，并用 50 MHz 计数确认 LP-11。
  always@(posedge Clk or negedge Rst_n)
  if(~Rst_n)begin
    lp_clk_meta <= 2'b00;
    lp_clk_sync <= 2'b00;
    probe_state <= LP11_PROBE_ACTIVE ? PROBE_STOP : PROBE_RUN;
    probe_stop_index <= 2'd0;
    probe_quiet_count <= 32'd0;
    probe_reset_release_count <= 8'd0;
    probe_fault <= 1'b0;
    probe_lp11_seen <= 1'b0;
    probe_lp_clk00_count <= 2'd0;
    probe_rx_release_done <= 1'b0;
  end
  else begin
    lp_clk_meta <= lp_clk_state;
    lp_clk_sync <= lp_clk_meta;
    if(LP11_PROBE_ACTIVE)begin
      if(RW_Done && ack)begin
        probe_fault <= 1'b1;
        probe_state <= PROBE_FAULT;
        probe_quiet_count <= 32'd0;
      end
      else begin
        case(probe_state)
          PROBE_STOP:
            if((cnt == 8'd82) && RW_Done && (!ack))begin
              if(probe_stop_index == 2'd2)begin
                probe_stop_index <= 2'd0;
                probe_quiet_count <= 32'd0;
                probe_state <= PROBE_WAIT_LP11;
              end
              else
                probe_stop_index <= probe_stop_index + 1'b1;
            end
          PROBE_WAIT_LP11:
            if(lp_clk_sync == 2'b11)begin
              if(probe_quiet_count >= LP11_QUIET_CYCLES - 1)begin
                probe_quiet_count <= 32'd0;
                probe_state <= PROBE_HOLD_LP11;
              end
              else
                probe_quiet_count <= probe_quiet_count + 1'b1;
            end
            else
              probe_quiet_count <= 32'd0;
          PROBE_HOLD_LP11:
            if(lp_clk_sync == 2'b11)begin
              if(probe_quiet_count >= LP11_QUIET_CYCLES - 1)begin
                probe_quiet_count <= 32'd0;
                probe_state <= PROBE_RUN;
              end
              else
                probe_quiet_count <= probe_quiet_count + 1'b1;
            end
            else begin
              // LP-11 在第二段保持窗口中断时，先重新断言接收器复位再从头计时。
              probe_quiet_count <= 32'd0;
              probe_state <= PROBE_WAIT_LP11;
            end
          default:
            probe_quiet_count <= 32'd0;
        endcase

        // WAIT 完成完整 1 ms LP-11 窗口后才允许后续流启动触发 D-PHY 释放。
        if((probe_state == PROBE_WAIT_LP11) &&
           (lp_clk_sync == 2'b11) &&
           (probe_quiet_count >= LP11_QUIET_CYCLES - 1))
          probe_lp11_seen <= 1'b1;

        // I2C 初始化独立运行在 50 MHz；整表完成后，需观测 LP-11 后连续三拍 LP-clock=00。
        // 释放只锁存一次；释放后的 LP-11 返回不会重新断言接收器复位。
        if(!probe_rx_release_done)begin
          if((probe_state == PROBE_RUN) && !probe_fault && probe_lp11_seen &&
             Init_Done && (lp_clk_sync == 2'b00))begin
            if(probe_lp_clk00_count == 2'd2)begin
              probe_rx_release_done <= 1'b1;
              probe_reset_release_count <= probe_reset_release_count + 1'b1;
            end
            else
              probe_lp_clk00_count <= probe_lp_clk00_count + 1'b1;
          end
          else
            probe_lp_clk00_count <= 2'd0;
        end
      end
    end
    else begin
      probe_state <= PROBE_RUN;
      probe_stop_index <= 2'd0;
      probe_quiet_count <= 32'd0;
      probe_reset_release_count <= 8'd0;
      probe_fault <= 1'b0;
      probe_lp11_seen <= 1'b0;
      probe_lp_clk00_count <= 2'd0;
      probe_rx_release_done <= 1'b0;
    end
  end


  i2c_control #(
    .SYS_CLOCK (SYS_CLOCK ),
    .SCL_CLOCK (SCL_CLOCK )
  )i2c_control(
    .Clk         (Clk             ),
    .Rst_n       (Rst_n           ),
    .wrreg_req   (wrreg_req       ),
    .rdreg_req   (1'd0            ),
    .addr        (addr            ),
    .addr_mode   (addr_mode       ),
    .wrdata      (wrdata          ),
    .rddata      (rddata          ),
    .device_id   (device_id       ),
    .RW_Done     (RW_Done         ),
    .ack         (ack             ),
    .dly_cnt_max (i2c_dly_cnt_max ),
    .i2c_sclk    (i2c_sclk        ),
    .i2c_sdat    (i2c_sdat        )
  );

  wire Go;   //initial enable
  reg [20:0] delay_cnt;

  //上电并复位完成20ms后再配置摄像头，所以从上电到开始配置应该是1 + 20 = 21ms
  always@(posedge Clk or negedge Rst_n)
  if(~Rst_n)
    delay_cnt <= 21'd0;
  else if (delay_cnt >= DELAY_21ms_CNT)
    delay_cnt <= DELAY_21ms_CNT;
  else
    delay_cnt <= delay_cnt + 1'd1;

  //当延时时间到，开始使能初始化模块对OV5647的寄存器进行写入
  assign Go = (delay_cnt == DELAY_21ms_CNT - 1'b1) ? 1'b1 : 1'b0;

  //摄像头上电后保持复位1ms，所以上电后需要1ms之后再使能释放摄像头的复位信号
  //这里为了优化逻辑，简化比较器逻辑，直接使延迟比较值为DELAY_1ms_CNT
  assign camera_rst_n = (delay_cnt > DELAY_1ms_CNT);

  always@(posedge Clk or negedge Rst_n)
  if(~Rst_n)
    cnt <= 0;
  else if(Go)
    cnt <= 0;
  else if(cnt < lut_size)begin
    if(RW_Done && (!ack))begin
      if(LP11_PROBE_ACTIVE && (cnt == 8'd82) && (probe_state != PROBE_RUN))
        cnt <= cnt;
      else
        cnt <= cnt + 1'b1;
    end
    else
      cnt <= cnt;
  end
  else
    cnt <= 0;

  always@(posedge Clk or negedge Rst_n)
  if(~Rst_n)
    Init_Done <= 0;
  else if(Go)
    Init_Done <= 0;
  else if(LP11_PROBE_ACTIVE && probe_fault)
    Init_Done <= 0;
  else if(cnt == lut_size)
    Init_Done <= 1;

  reg [1:0]state;

  always@(posedge Clk or negedge Rst_n)
  if(~Rst_n)begin
    state <= 0;
    wrreg_req <= 1'b0;
    i2c_dly_cnt_max <= 32'd0;
  end
  else if(LP11_PROBE_ACTIVE && probe_fault)begin
    wrreg_req <= 1'b0;
    state <= 1;
  end
  else if(LP11_PROBE_ACTIVE && (cnt == 8'd82) &&
          ((probe_state == PROBE_WAIT_LP11) || (probe_state == PROBE_HOLD_LP11)))begin
    wrreg_req <= 1'b0;
    state <= 1;
  end
  else if(cnt < lut_size)begin
    case(state)
      0:
        if(Go)
          state <= 1;
        else
          state <= 0;
      1:
        begin
          wrreg_req <= 1'b1;
          state <= 2;
          if(cnt == 1)
            i2c_dly_cnt_max <= DELAY_5ms_CNT; //延时5ms
          else
            i2c_dly_cnt_max <= 32'd0;
        end
      2:
        begin
          wrreg_req <= 1'b0;
          if(RW_Done)
            state <= 1;
          else
            state <= 2;
        end
      default:state <= 0;
    endcase
  end
  else
    state <= 0;

endmodule
