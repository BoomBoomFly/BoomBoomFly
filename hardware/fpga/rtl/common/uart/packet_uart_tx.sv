// Integrated UART support: packet_uart_tx.v
`timescale 1ns/1ps

// 固定长度报文串行发送器；锁存完整帧后逐字节输出，忙期间不接收新帧。
module packet_uart_tx #(
    parameter integer PACKET_BYTES = 32
) (
    input  wire         clk,
    input  wire         rst,
    input  wire         packet_valid_i,
    input  wire [PACKET_BYTES*8-1:0] packet_data_i,
    output wire         packet_ready_o,
    input  wire         uart_busy_i,
    output reg  [7:0]   uart_data_o,
    output reg          uart_start_o,
    output wire         packet_pending_o
);
    reg [PACKET_BYTES*8-1:0] shift_reg;
    localparam integer INDEX_WIDTH = (PACKET_BYTES > 1) ? $clog2(PACKET_BYTES) : 1;
    reg [INDEX_WIDTH-1:0] byte_index;
    reg pending;
    reg active;

    assign packet_ready_o = !pending && !active;
    assign packet_pending_o = pending || active;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            shift_reg    <= {PACKET_BYTES*8{1'b0}};
            byte_index   <= {INDEX_WIDTH{1'b0}};
            pending      <= 1'b0;
            active       <= 1'b0;
            uart_data_o  <= 8'd0;
            uart_start_o <= 1'b0;
        end else begin
            uart_start_o <= 1'b0;
            if (!active) begin
                if (pending) begin
                    if (!uart_busy_i) begin
                        uart_data_o  <= shift_reg[PACKET_BYTES*8-1 -: 8];
                        uart_start_o <= 1'b1;
                        active       <= 1'b1;
                        pending      <= 1'b0;
                        byte_index   <= {INDEX_WIDTH{1'b0}};
                    end
                end else if (packet_valid_i) begin
                    shift_reg <= packet_data_i;
                    pending   <= 1'b1;
                end
            end else begin
                if (uart_start_o) begin
                    uart_start_o <= 1'b0;
                end else if (!uart_busy_i) begin
                    if (byte_index == PACKET_BYTES - 1) begin
                        active     <= 1'b0;
                        byte_index <= {INDEX_WIDTH{1'b0}};
                    end else begin
                        shift_reg    <= shift_reg << 8;
                        uart_data_o  <= (shift_reg << 8) >> (PACKET_BYTES*8-8);
                        uart_start_o <= 1'b1;
                        byte_index   <= byte_index + 1'b1;
                    end
                end
            end
        end
    end
endmodule
