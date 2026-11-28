// ==================== eth_udp_rx_gmii.v ====================
/////////////////////////////////////////////////////////////////////////////////
// Company       : 武汉芯路恒科技有限公司
//                 http://xiaomeige.taobao.com
// Web           : http://www.corecourse.cn
//
// Create Date   : 2019/05/01 00:00:00
// Module Name   : eth_udp_rx_gmii
// Description   : 以太网接收模块，gmii接口
//
// Dependencies  :
//
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
//
/////////////////////////////////////////////////////////////////////////////////

module eth_udp_rx_gmii(
  reset_p,

  local_mac,
  local_ip,
  local_port,

  clk125m_o,
  exter_mac,
  exter_ip,
  exter_port,
  rx_data_length,
  data_overflow_i,
  payload_valid_o,
  payload_dat_o,

  one_pkt_done,
  pkt_error,
  debug_crc_check,

  gmii_rx_clk,
  gmii_rxdv,
  gmii_rxd,
  rx_reset_stage0_i,
  rx_async_reset_p_i
);
  input              reset_p;

  input     [47:0]   local_mac;
  input     [31:0]   local_ip;
  input     [15:0]   local_port;

  output             clk125m_o;
  output reg[47:0]   exter_mac;
  output reg[31:0]   exter_ip;
  output reg[15:0]   exter_port;
  output reg[15:0]   rx_data_length;
  input              data_overflow_i;
  output reg         payload_valid_o;
  output reg[7:0]    payload_dat_o;

  output reg         one_pkt_done;
  output reg         pkt_error;
  output    [31:0]   debug_crc_check;

  input        gmii_rx_clk;
  (*IOB = "TRUE"*) input  [7:0] gmii_rxd;
  (*IOB = "TRUE"*) input        gmii_rxdv;
  input              rx_reset_stage0_i;
  input              rx_async_reset_p_i;

  parameter ETH_type       = 16'h0800,
            IP_ver         = 4'h4,
            IP_hdr_len     = 4'h5,
            IP_protocol    = 8'h11;
  parameter ACCEPT_BROADCAST_MAC = 1'b1;
  // 默认共享原 reset，旧实例不连接新增端口时行为保持不变。
  parameter SPLIT_IP_CHECKSUM_RESET = 1'b0;

  localparam
    IDLE              = 12'b000000000001,
    RX_PREAMBLE       = 12'b000000000010,
    RX_ETH_HEADER     = 12'b000000000100,
    RX_IP_HEADER      = 12'b000000001000,
    RX_UDP_HEADER     = 12'b000000010000,
    RX_DATA           = 12'b000000100000,
    RX_DRP_DATA       = 12'b000001000000,
    RX_CRC            = 12'b000010000000,
    UDP_CHECKSUM_SUM  = 12'b000100000000,
    UDP_CHECKSUM_FOLD = 12'b001000000000,
    UDP_CHECKSUM_TEST = 12'b010000000000,
    PKT_CHECK         = 12'b100000000000;

  wire        clk125m;
  reg  [7:0]  reg_gmii_rxd;
  reg         reg_gmii_rxdv;
  reg  [7:0]  rx_data_dly1;
  reg  [7:0]  rx_data_dly2;
  reg         rx_datav_dly1;
  reg         rx_datav_dly2;
  reg  [47:0] local_mac_reg;
  reg  [31:0] local_ip_reg;
  reg  [15:0] local_port_reg;
  reg  [11:0] curr_state;
  reg  [11:0] next_state;

  reg         reg_data_overflow;

  reg  [47:0] rx_dst_mac;
  reg  [47:0] rx_src_mac;
  reg  [15:0] rx_eth_type;
  reg         eth_header_check_ok;

  reg  [3:0]  rx_ip_ver;
  reg  [3:0]  rx_ip_hdr_len;
  reg  [7:0]  rx_ip_tos;
  reg  [15:0] rx_total_len;
  reg  [15:0] rx_ip_id;
  reg         rx_ip_rsv;
  reg         rx_ip_df;
  reg         rx_ip_mf;
  reg  [12:0] rx_ip_frag_offset;
  reg  [7:0]  rx_ip_ttl;
  reg  [7:0]  rx_ip_protocol;
  reg  [15:0] rx_ip_check_sum;
  reg  [31:0] rx_src_ip;
  reg  [31:0] rx_dst_ip;
  reg         ip_checksum_cal_en;
  wire [15:0] cal_check_sum;
  wire        ip_checksum_done;
  reg         ip_header_check_ok;
  wire        ip_checksum_reset_p;

  generate
    if (SPLIT_IP_CHECKSUM_RESET) begin : g_ip_checksum_reset_split
      // D 取 RX reset synchronizer 的 stage0，和主 stage1 同源同拍释放。
      // 保留副本使综合器不把局部 reset 合并回高扇出的主 stage1。
      (* ASYNC_REG="TRUE", syn_keep=1, syn_preserve=1 *) reg ip_checksum_reset_stage1_q;
      always @(posedge clk125m or posedge rx_async_reset_p_i)
        if (rx_async_reset_p_i) ip_checksum_reset_stage1_q <= 1'b1;
        else ip_checksum_reset_stage1_q <= rx_reset_stage0_i;
      assign ip_checksum_reset_p = ip_checksum_reset_stage1_q;
    end else begin : g_ip_checksum_reset_shared
      assign ip_checksum_reset_p = reset_p;
    end
  endgenerate

  reg  [15:0] rx_src_port;
  reg  [15:0] rx_dst_port;
  reg  [15:0] rx_udp_length;
  reg  [15:0] rx_udp_checksum;
  reg         udp_header_check_ok;
  reg  [16:0] udp_checksum_sum;
  reg  [7:0]  udp_checksum_high_byte;
  reg         udp_checksum_odd_byte;
  reg  [16:0] udp_checksum_total_q;
  reg         udp_checksum_ok_q;
  reg         frame_truncated;

  reg         crc_init;
  reg         crc_en;
  reg  [7:0]  crc_data;
  wire [31:0] crc_check;

  reg  [3:0]  cnt_preamble;
  reg  [3:0]  cnt_eth_header;
  reg  [4:0]  cnt_ip_header;
  reg  [3:0]  cnt_udp_header;
  reg  [15:0] cnt_data;
  reg         cnt_data_upper_increment;
  reg  [4:0]  cnt_drp_data;
  // Payload boundary arithmetic is prepared while the IPv4 header is still
  // arriving, so the RX state transition only compares registered values.
  reg  [15:0] rx_payload_length_stage;
  reg  [15:0] rx_data_last_count;
  reg  [4:0]  rx_drop_last_count;
  reg         rx_payload_is_short;

  assign clk125m_o = clk125m;
  assign debug_crc_check = crc_check;

//  BUFG BUFG_pclk (
//    .O(clk125m        ), // 1-bit output: Clock output
//    .I(gmii_rx_clk    )  // 1-bit input: Clock input
//  );

  assign clk125m = gmii_rx_clk;

  //将本地MAC、IP、PORT寄存
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    local_mac_reg  <= 48'h00_00_00_00_00_00;
    local_ip_reg   <= 32'h00_00_00_00;
    local_port_reg <= 16'h00_00;
  end
  else if(curr_state == IDLE)
  begin
    local_mac_reg  <= local_mac;
    local_ip_reg   <= local_ip;
    local_port_reg <= local_port;
  end

  //将以太网输入的接收信号寄存
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    reg_gmii_rxd  <= 8'h00;
    reg_gmii_rxdv <= 1'b0;
  end
  else
  begin
    reg_gmii_rxd  <= gmii_rxd;
    reg_gmii_rxdv <= gmii_rxdv;
  end

  //将以太网输入的接收信号寄存后打拍
  always@(posedge clk125m)
  begin
    rx_data_dly1  <= reg_gmii_rxd;
    rx_data_dly2  <= rx_data_dly1;
    rx_datav_dly1 <= reg_gmii_rxdv;
    rx_datav_dly2 <= rx_datav_dly1;
  end

  //cnt_preamble
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    cnt_preamble <= 4'd0;
  else if(curr_state == RX_PREAMBLE && rx_data_dly2 == 8'h55)
    cnt_preamble <= cnt_preamble + 1'b1;
  else
    cnt_preamble <= 4'd0;

  //cnt_eth_header
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    cnt_eth_header <= 4'd0;
  else if(curr_state == RX_ETH_HEADER)
    cnt_eth_header <= cnt_eth_header + 1'b1;
  else
    cnt_eth_header <= 4'd0;

  // Destination MAC is only inspected after all six bytes have arrived, so
  // it does not need the high-fanout asynchronous parser reset.
  always@(posedge clk125m)
  if(curr_state == RX_ETH_HEADER)
  begin
    case(cnt_eth_header)
      4'd0 :rx_dst_mac[47:40] <= rx_data_dly2;
      4'd1 :rx_dst_mac[39:32] <= rx_data_dly2;
      4'd2 :rx_dst_mac[31:24] <= rx_data_dly2;
      4'd3 :rx_dst_mac[23:16] <= rx_data_dly2;
      4'd4 :rx_dst_mac[15:8]  <= rx_data_dly2;
      4'd5 :rx_dst_mac[7:0]   <= rx_data_dly2;
      default: ;
    endcase
  end

  always@(posedge clk125m or posedge reset_p)
  if(reset_p) begin
    rx_src_mac  <= 48'h00_00_00_00_00_00;
    rx_eth_type <= 16'h0000;
  end else if(curr_state == RX_ETH_HEADER)
  begin
    case(cnt_eth_header)

      4'd6 :rx_src_mac[47:40] <= rx_data_dly2;
      4'd7 :rx_src_mac[39:32] <= rx_data_dly2;
      4'd8 :rx_src_mac[31:24] <= rx_data_dly2;
      4'd9 :rx_src_mac[23:16] <= rx_data_dly2;
      4'd10:rx_src_mac[15:8]  <= rx_data_dly2;
      4'd11:rx_src_mac[7:0]   <= rx_data_dly2;

      4'd12:rx_eth_type[15:8] <= rx_data_dly2;
      4'd13:rx_eth_type[7:0]  <= rx_data_dly2;
      default: ;
    endcase
  end

  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    eth_header_check_ok <= 1'b0;
  else if(rx_eth_type == ETH_type &&
          (rx_dst_mac == local_mac_reg ||
           (ACCEPT_BROADCAST_MAC && rx_dst_mac == 48'hFF_FF_FF_FF_FF_FF)))
    eth_header_check_ok <= 1'b1;
  else
    eth_header_check_ok <= 1'b0;

  //cnt_ip_header
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    cnt_ip_header <= 5'd0;
  else if(curr_state == RX_IP_HEADER)
    cnt_ip_header <= cnt_ip_header + 1'b1;
  else
    cnt_ip_header <= 5'd0;

  //ip_header
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    {rx_ip_ver,rx_ip_hdr_len}     <= 8'h0;
    rx_ip_tos                     <= 8'h0;
    rx_total_len                  <= 16'h0;
    rx_ip_id                      <= 16'h0;
    {rx_ip_rsv,rx_ip_df,rx_ip_mf} <= 3'h0;
    rx_ip_frag_offset             <= 13'h0;
    rx_ip_ttl                     <= 8'h0;
    rx_ip_protocol                <= 8'h0;
    rx_ip_check_sum               <= 16'h0;
    rx_src_ip                     <= 32'h0;
    rx_dst_ip                     <= 32'h0;
  end
  else if(curr_state == RX_IP_HEADER)
  begin
    case(cnt_ip_header)
      5'd0:   {rx_ip_ver,rx_ip_hdr_len}                             <= rx_data_dly2;
      5'd1:   rx_ip_tos                                             <= rx_data_dly2;
      5'd2:   rx_total_len[15:8]                                    <= rx_data_dly2;
      5'd3:   rx_total_len[7:0]                                     <= rx_data_dly2;
      5'd4:   rx_ip_id[15:8]                                        <= rx_data_dly2;
      5'd5:   rx_ip_id[7:0]                                         <= rx_data_dly2;
      5'd6:   {rx_ip_rsv,rx_ip_df,rx_ip_mf,rx_ip_frag_offset[12:8]} <= rx_data_dly2;
      5'd7:   rx_ip_frag_offset[7:0]                                <= rx_data_dly2;
      5'd8:   rx_ip_ttl                                             <= rx_data_dly2;
      5'd9:   rx_ip_protocol                                        <= rx_data_dly2;
      5'd10:  rx_ip_check_sum[15:8]                                 <= rx_data_dly2;
      5'd11:  rx_ip_check_sum[7:0]                                  <= rx_data_dly2;
      5'd12:  rx_src_ip[31:24]                                      <= rx_data_dly2;
      5'd13:  rx_src_ip[23:16]                                      <= rx_data_dly2;
      5'd14:  rx_src_ip[15:8]                                       <= rx_data_dly2;
      5'd15:  rx_src_ip[7:0]                                        <= rx_data_dly2;
      5'd16:  rx_dst_ip[31:24]                                      <= rx_data_dly2;
      5'd17:  rx_dst_ip[23:16]                                      <= rx_data_dly2;
      5'd18:  rx_dst_ip[15:8]                                       <= rx_data_dly2;
      5'd19:  rx_dst_ip[7:0]                                        <= rx_data_dly2;
      default: ;
    endcase
  end

  //udp_header: 8byte
  //ip_header: 20byte
  //rx_data_length = rx_total_len - udp_header - ip_header;
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    rx_data_length <= 16'd0;
    rx_payload_length_stage <= 16'd0;
    rx_data_last_count <= 16'hffff;
    rx_drop_last_count <= 5'd0;
    rx_payload_is_short <= 1'b0;
  end
  else begin
    // Count 3 is the final byte of IPv4 total_length.  Use the registered
    // high byte and incoming low byte, then derive terminal counters one
    // clock later while the rest of the IP header is being parsed.
    if(curr_state == RX_IP_HEADER && cnt_ip_header == 5'd3)
      rx_payload_length_stage <= {rx_total_len[15:8],rx_data_dly2} - 16'd28;
    if(curr_state == RX_IP_HEADER && cnt_ip_header == 5'd4) begin
      rx_data_last_count <= rx_payload_length_stage - 16'd1;
      rx_drop_last_count <= 5'd17 - rx_payload_length_stage[4:0];
      rx_payload_is_short <= rx_payload_length_stage < 16'd18;
    end
    if(curr_state == RX_IP_HEADER && cnt_ip_header == 5'd19)
      rx_data_length <= rx_total_len - 8'd20 - 8'd8;
  end

  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    ip_checksum_cal_en <= 1'b0;
  else if(curr_state == RX_IP_HEADER && cnt_ip_header == 5'd19)
    ip_checksum_cal_en <= 1'b1;
  else
    ip_checksum_cal_en <= 1'b0;

  ip_checksum ip_checksum(
    .clk            (clk125m           ),
    .reset_p        (ip_checksum_reset_p),

    .cal_en         (ip_checksum_cal_en),

    .IP_ver         (rx_ip_ver         ),
    .IP_hdr_len     (rx_ip_hdr_len     ),
    .IP_tos         (rx_ip_tos         ),
    .IP_total_len   (rx_total_len      ),
    .IP_id          (rx_ip_id          ),
    .IP_rsv         (rx_ip_rsv         ),
    .IP_df          (rx_ip_df          ),
    .IP_mf          (rx_ip_mf          ),
    .IP_frag_offset (rx_ip_frag_offset ),
    .IP_ttl         (rx_ip_ttl         ),
    .IP_protocol    (rx_ip_protocol    ),
    .src_ip         (rx_src_ip         ),
    .dst_ip         (rx_dst_ip         ),

    .checksum       (cal_check_sum     ),
    .cal_done_o     (ip_checksum_done  )
  );

  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    ip_header_check_ok <= 1'b0;
  else if(ip_checksum_done &&
          {IP_ver,IP_hdr_len,IP_protocol,cal_check_sum,local_ip_reg} ==
          {rx_ip_ver,rx_ip_hdr_len,rx_ip_protocol,rx_ip_check_sum,rx_dst_ip} &&
          !rx_ip_rsv && !rx_ip_mf && rx_ip_frag_offset == 13'd0 &&
          rx_total_len >= 16'd28)
    ip_header_check_ok <= 1'b1;
  else
    ip_header_check_ok <= 1'b0;

  //cnt_udp_header
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    cnt_udp_header <= 4'd0;
  else if(curr_state == RX_UDP_HEADER)
    cnt_udp_header <= cnt_udp_header + 1'b1;
  else
    cnt_udp_header <= 4'd0;

  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    rx_src_port  <= 16'h0;
    rx_dst_port  <= 16'h0;
    rx_udp_length<= 16'h0;
    rx_udp_checksum <= 16'h0;
  end
  else if(curr_state == RX_UDP_HEADER)
  begin
    case(cnt_udp_header)
      4'd0: rx_src_port[15:8]   <= rx_data_dly2;
      4'd1: rx_src_port[7:0]    <= rx_data_dly2;
      4'd2: rx_dst_port[15:8]   <= rx_data_dly2;
      4'd3: rx_dst_port[7:0]    <= rx_data_dly2;
      4'd4: rx_udp_length[15:8] <= rx_data_dly2;
      4'd5: rx_udp_length[7:0]  <= rx_data_dly2;
      4'd6: rx_udp_checksum[15:8] <= rx_data_dly2;
      4'd7: rx_udp_checksum[7:0]  <= rx_data_dly2;
      default: ;
    endcase
  end

  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    udp_header_check_ok <= 1'b0;
  else if(rx_dst_port == local_port_reg && rx_udp_length >= 16'd8 &&
          rx_udp_length == (rx_total_len - 16'd20))
    udp_header_check_ok <= 1'b1;
  else
    udp_header_check_ok <= 1'b0;

  //cnt_data
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    cnt_data <= 16'd0;
    cnt_data_upper_increment <= 1'b0;
  end
  else if(curr_state == RX_DATA)
  begin
    cnt_data[7:0] <= cnt_data[7:0] + 1'b1;
    cnt_data[15:8] <= cnt_data[15:8] + cnt_data_upper_increment;
    cnt_data_upper_increment <= cnt_data[7:0] == 8'hfe;
  end
  else
  begin
    cnt_data <= 16'd0;
    cnt_data_upper_increment <= 1'b0;
  end

  //cnt_drp_data
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    cnt_drp_data <= 5'd0;
  else if(curr_state == RX_DRP_DATA)
    cnt_drp_data <= cnt_drp_data + 1'b1;
  else
    cnt_drp_data <= 5'd0;

  // IPv4 允许 UDP checksum 为零；非零值必须覆盖伪首部、UDP 首部和负载。
  // 伪首部随 IP 字节分拍累加，避免目的 IP 一次穿过多级加法器。
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    udp_checksum_sum       <= 17'd0;
    udp_checksum_high_byte <= 8'd0;
    udp_checksum_odd_byte  <= 1'b0;
  end
  else if(curr_state == RX_IP_HEADER && cnt_ip_header == 5'd15)
  begin
    udp_checksum_sum <= {1'b0, rx_src_ip[31:16]} +
                        {1'b0, rx_src_ip[15:8], rx_data_dly2};
    udp_checksum_high_byte <= 8'd0;
    udp_checksum_odd_byte  <= 1'b0;
  end
  else if(curr_state == RX_IP_HEADER && cnt_ip_header == 5'd17)
    udp_checksum_sum <= {1'b0, udp_checksum_sum[15:0]} +
                        {1'b0, rx_dst_ip[31:24], rx_data_dly2} +
                        udp_checksum_sum[16];
  else if(curr_state == RX_IP_HEADER && cnt_ip_header == 5'd19)
    udp_checksum_sum <= {1'b0, udp_checksum_sum[15:0]} +
                        {1'b0, rx_dst_ip[15:8], rx_data_dly2} +
                        udp_checksum_sum[16];
  else if(curr_state == RX_UDP_HEADER && cnt_udp_header == 4'd0)
  begin
    udp_checksum_sum <= {1'b0, udp_checksum_sum[15:0]} +
                        {9'd0, IP_protocol} + udp_checksum_sum[16];
    udp_checksum_high_byte <= rx_data_dly2;
    udp_checksum_odd_byte  <= 1'b1;
  end
  else if(curr_state == RX_UDP_HEADER || curr_state == RX_DATA)
  begin
    if(udp_checksum_odd_byte)
    begin
      udp_checksum_sum <= {1'b0, udp_checksum_sum[15:0]} +
                          {1'b0, udp_checksum_high_byte, rx_data_dly2} +
                          udp_checksum_sum[16];
      udp_checksum_odd_byte <= 1'b0;
    end
    else
    begin
      udp_checksum_high_byte <= rx_data_dly2;
      udp_checksum_odd_byte  <= 1'b1;
    end
  end

  // 帧尾加入长度。奇数字节只占高8位；校验和为全1时，
  // 低8位加进位必须等于ff且不产生进位，高8位与奇数字节互补。
  // 因此可直接比较两个字节，无需再串联16位进位链。
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    udp_checksum_total_q <= 17'd0;
    udp_checksum_ok_q    <= 1'b0;
  end
  else
  begin
    if(curr_state == UDP_CHECKSUM_SUM)
      udp_checksum_total_q <= {1'b0, udp_checksum_sum[15:0]} +
        {1'b0, rx_udp_length} + udp_checksum_sum[16];
    if(curr_state == UDP_CHECKSUM_FOLD)
      udp_checksum_ok_q <= (rx_udp_checksum == 16'h0000) ||
        ((udp_checksum_total_q[7:0] == (udp_checksum_total_q[16] ? 8'hfe : 8'hff)) &&
         (udp_checksum_total_q[15:8] ==
          (udp_checksum_odd_byte ? ~udp_checksum_high_byte : 8'hff)));
  end

  //FSM
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    curr_state <= IDLE;
  else
    curr_state <= next_state;

  always@(*)
  begin
    case(curr_state)
      IDLE:
        if(!rx_datav_dly2 && rx_datav_dly1)
          next_state = RX_PREAMBLE;
        else
          next_state = IDLE;

      RX_PREAMBLE:
        if(rx_data_dly2 == 8'hd5 && cnt_preamble > 4'd5)
          next_state = RX_ETH_HEADER;
        else if(cnt_preamble > 4'd7)
          next_state = IDLE;
        else
          next_state = RX_PREAMBLE;

      RX_ETH_HEADER:
        if(cnt_eth_header == 4'd13)
          next_state = RX_IP_HEADER;
        else
          next_state = RX_ETH_HEADER;

      RX_IP_HEADER:
        if(cnt_ip_header == 5'd2 && eth_header_check_ok == 1'b0)
          next_state = IDLE;
        else if(cnt_ip_header == 5'd19)
          next_state = RX_UDP_HEADER;
        else
          next_state = RX_IP_HEADER;

      RX_UDP_HEADER:
        // ip_checksum 的部分和/折叠均分拍，到第 6 个 UDP 首部字节前裁决。
        if(cnt_udp_header == 4'd5 && ip_header_check_ok == 1'b0)
          next_state = IDLE;
        else if(cnt_udp_header == 4'd7 && udp_header_check_ok == 1'b0)
          next_state = IDLE;
        else if(cnt_udp_header == 4'd7)
          next_state = RX_DATA;
        else
          next_state = RX_UDP_HEADER;

      RX_DATA:
        if(rx_payload_is_short && (cnt_data == rx_data_last_count))
          next_state = RX_DRP_DATA;
        else if(cnt_data == rx_data_last_count)
          next_state = RX_CRC;
        else
          next_state = RX_DATA;

      RX_DRP_DATA:
        if(cnt_drp_data == rx_drop_last_count)
          next_state = RX_CRC;
        else
          next_state = RX_DRP_DATA;

      RX_CRC:
        if(rx_datav_dly2 == 1'b0)
          next_state = UDP_CHECKSUM_SUM;
        else
          next_state = RX_CRC;

      UDP_CHECKSUM_SUM:
        next_state = UDP_CHECKSUM_FOLD;

      UDP_CHECKSUM_FOLD:
        next_state = UDP_CHECKSUM_TEST;

      UDP_CHECKSUM_TEST:
        next_state = PKT_CHECK;

      PKT_CHECK:
        next_state = IDLE;

      default:next_state = IDLE;

    endcase
    // 帧中途撤销 RX_DV 必须结束本帧；不能按伪造长度继续吞掉下一帧。
    if(!rx_datav_dly2 && (curr_state==RX_PREAMBLE || curr_state==RX_ETH_HEADER ||
       curr_state==RX_IP_HEADER || curr_state==RX_UDP_HEADER ||
       curr_state==RX_DATA || curr_state==RX_DRP_DATA))
      next_state=PKT_CHECK;
  end

  always @(posedge clk125m or posedge reset_p)
    if(reset_p)frame_truncated<=1'b0;
    else if(curr_state==IDLE)frame_truncated<=1'b0;
    else if(!rx_datav_dly2 && (curr_state==RX_PREAMBLE || curr_state==RX_ETH_HEADER ||
       curr_state==RX_IP_HEADER || curr_state==RX_UDP_HEADER ||
       curr_state==RX_DATA || curr_state==RX_DRP_DATA))frame_truncated<=1'b1;

  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    crc_init <= 1'b0;
  else if (rx_datav_dly1 && (~rx_datav_dly2))
    crc_init <= 1'b1;
  else
    crc_init <= 1'b0;

  //crc_en
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    crc_en <= 1'b0;
  else if(curr_state == IDLE)
    crc_en <= 1'b0;
  else if (curr_state != RX_PREAMBLE && rx_datav_dly2)
    crc_en <= 1'b1;
  else
    crc_en <= 1'b0;

  //crc_data
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    crc_data <= 8'd0;
  else
    crc_data <= rx_data_dly2;

  crc32_d8 crc32_d8
  (
    .clk         (clk125m       ),
    .reset_p     (reset_p       ),

    .data        (crc_data      ),
    .crc_init    (crc_init      ),
    .crc_en      (crc_en        ),
    .crc_result  (crc_check     )//latency=1
  );

  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
    reg_data_overflow <= 1'b0;
  else if(curr_state == IDLE)
    reg_data_overflow <= 1'b0;
  else if(curr_state == RX_DATA && data_overflow_i == 1'b1)
    reg_data_overflow <= 1'b1;
  else
    reg_data_overflow <= reg_data_overflow;

  //payload output
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    payload_valid_o <= 1'b0;
    payload_dat_o   <= 8'h0;
  end
  else if(curr_state == RX_DATA)
  begin
    payload_valid_o <= 1'b1;
    payload_dat_o   <= rx_data_dly2;
  end
  else
  begin
    payload_valid_o <= 1'b0;
    payload_dat_o   <= 8'h0;
  end

  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    exter_mac  <= 48'h0;
    exter_ip   <= 32'h0;
    exter_port <= 16'h0;
  end
  else if(curr_state == PKT_CHECK)
  begin
    exter_mac  <= rx_src_mac;
    exter_ip   <= rx_src_ip;
    exter_port <= rx_src_port;
  end

  //done
  always@(posedge clk125m or posedge reset_p)
  if(reset_p)
  begin
    one_pkt_done <= 1'b0;
    pkt_error    <= 1'b0;
  end
  else if(curr_state == PKT_CHECK)
  begin
    one_pkt_done <= 1'b1;
    if(crc_check == 32'h2144DF1C && reg_data_overflow == 1'b0 &&
       udp_header_check_ok && udp_checksum_ok_q && !frame_truncated)
      pkt_error  <= 1'b0;
    else
      pkt_error  <= 1'b1;
  end
  else
  begin
    one_pkt_done <= 1'b0;
    pkt_error    <= 1'b0;
  end

endmodule
