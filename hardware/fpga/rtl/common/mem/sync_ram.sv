// ==================== sync_ram.sv ====================
`timescale 1ns/1ps
// 导航片上RAM：同一时钟的A读/写口与B只读口，无数据复位或隐式初始化。
// 地址/使能在上升沿采样，读值在该沿NBA更新，顺序消费者从下一沿消费。
// A写入时A读输出保持；禁用端口输出保持。控制器必须禁止A写与B同址读。
module sync_ram #(
    parameter integer DATA_W=1,
    parameter integer ADDR_W=14
)(
    input wire clk,
    input wire a_en,a_we,
    input wire [ADDR_W-1:0] a_addr,
    input wire [DATA_W-1:0] a_wdata,
    output reg [DATA_W-1:0] a_rdata,
    input wire b_en,
    input wire [ADDR_W-1:0] b_addr,
    output reg [DATA_W-1:0] b_rdata
);
    // SUG550-2.4第5.16节：block_ram指定BSRAM；真实映射仍由综合报告确认。
    reg [DATA_W-1:0] mem [0:(1<<ADDR_W)-1] /* synthesis syn_ramstyle = "block_ram" */;
    always @(posedge clk) begin
        if(a_en) begin
            if(a_we) mem[a_addr]<=a_wdata;
            else a_rdata<=mem[a_addr];
        end
    end
    always @(posedge clk) begin
        if(b_en) b_rdata<=mem[b_addr];
    end
    // synthesis translate_off
    always @(posedge clk) begin
        if(a_en && a_we && b_en && a_addr==b_addr)
            $fatal(1,"双口同步 RAM 发生跨端口同址读写碰撞 addr=%0d",a_addr);
    end
    // synthesis translate_on
endmodule
