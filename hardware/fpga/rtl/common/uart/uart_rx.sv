// Integrated UART support: uart_rx.sv
`timescale 1ns/1ps

// 电机输入已由调用端同步；保留同步高有效复位和逐位数据输出。
module uart_rx #(
    parameter integer CLK_HZ=50_000_000,
    parameter integer BAUD=115200
)(
    input wire clk_i,rst_i,rx_i,
    output wire [7:0] data_o,
    output wire valid_o
);
    localparam integer BIT_CYCLES=CLK_HZ/BAUD;
    localparam integer HALF_CYCLES=(BIT_CYCLES/2<1)?1:BIT_CYCLES/2;
    uart_rx_core #(.BIT_CYCLES(BIT_CYCLES),.HALF_CYCLES(HALF_CYCLES),
        .ASYNC_RESET(0),.DATA_ON_SAMPLE(1)) receiver(
        .clk(clk_i),.reset_n(!rst_i),.rx_i(rx_i),.data_o(data_o),
        .valid_o(valid_o),.framing_error_o());
endmodule
