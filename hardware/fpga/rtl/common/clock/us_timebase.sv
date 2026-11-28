// ==================== us_timebase.sv ====================
`timescale 1ns/1ps
// 有理数微秒相位合同：支持任意 CLK_HZ（包括 1000 MHz / 30 = 33⅓ MHz）长期无累积漂移。
package clock_contract;
    function automatic integer phase_modulus(input integer hz);
        if(hz==33333333)phase_modulus=100;
        else if(hz%1000000==0)phase_modulus=hz/1000000;
        else phase_modulus=hz;
    endfunction
    function automatic integer phase_increment(input integer hz);
        if(hz==33333333)phase_increment=3;
        else if(hz%1000000==0)phase_increment=1;
        else phase_increment=1000000;
    endfunction
    function automatic integer phase_width(input integer hz);
        phase_width=$clog2(phase_modulus(hz)+phase_increment(hz));
        if(phase_width<1)phase_width=1;
    endfunction
endpackage

// 微秒时标先相减、再比较，避免32位借位链串入保护及大扇出控制。
// 提前1us判失效，覆盖两拍寄存延迟；valid撤销仍直接闭锁。
module deadline_age #(
    parameter integer TIMEOUT_US = 100000
)(
    input wire clk,rst,
    input wire [31:0] now_us_i,last_us_i,
    input wire valid_i,
    output reg [31:0] age_us_o,
    output wire fresh_o
);
    localparam [31:0] EARLY_LIMIT_US = TIMEOUT_US-1;
    reg fresh_q;
    always @(posedge clk) begin
        if(rst)begin age_us_o<=32'hffffffff;fresh_q<=0;end
        else begin
            age_us_o<=now_us_i-last_us_i;
            fresh_q<=valid_i&&(age_us_o<EARLY_LIMIT_US);
        end
    end
    assign fresh_o=valid_i&&fresh_q;
endmodule

// 共享下一相位与tick逻辑；状态仍由各时钟域持有，禁止直接跨域采样计数总线。
module us_phase #(
    parameter integer CLK_HZ=50000000,
    parameter integer WIDTH=clock_contract::phase_width(CLK_HZ)
)(
    input wire [WIDTH-1:0] phase_i,
    output wire [WIDTH-1:0] next_phase_o,
    output wire tick_o
);
    localparam integer MODULUS=clock_contract::phase_modulus(CLK_HZ);
    localparam integer INCREMENT=clock_contract::phase_increment(CLK_HZ);
    wire [WIDTH:0] next_sum={1'b0,phase_i}+INCREMENT;
    assign tick_o=next_sum>=MODULUS;
    wire [31:0] reduced_phase=tick_o ? next_sum-MODULUS : next_sum;
    // 正常相位小于MODULUS，WIDTH由MODULUS+INCREMENT确定，显式选取有效位。
    assign next_phase_o=reduced_phase[WIDTH-1:0];
endmodule
