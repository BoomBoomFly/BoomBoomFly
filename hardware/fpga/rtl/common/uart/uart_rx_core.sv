`timescale 1ns/1ps
// 通用 UART 接收核心；输入同步由调用端完成，支持参数化分频、复位方式与采样提交时刻。
module uart_rx_core #(
    parameter integer BIT_CYCLES=434,
    parameter integer HALF_CYCLES=BIT_CYCLES/2,
    parameter integer ASYNC_RESET=1,
    parameter integer DATA_ON_SAMPLE=0
)(
    input wire clk,reset_n,rx_i,
    output reg [7:0] data_o,
    output reg valid_o,framing_error_o
);
    localparam integer COUNT_W=(BIT_CYCLES<2)?1:$clog2(BIT_CYCLES+1);
    localparam [1:0] IDLE=0,START=1,DATA=2,STOP=3;

    reg [1:0] state;
    reg [COUNT_W-1:0] count;
    reg [2:0] bit_index;
    reg [7:0] shift;
    // 复位方式在展开期选择，使异步边沿与复位条件严格一致。
    task receive_step;
        begin

            valid_o<=0;framing_error_o<=0;
            case(state)
                IDLE: if(!rx_i) begin count<=HALF_CYCLES-1;state<=START;end
                START: begin
                    if(count!=0) count<=count-1'b1;
                    else if(!rx_i) begin bit_index<=0;count<=BIT_CYCLES-1;state<=DATA;end
                    else state<=IDLE;
                end
                DATA: begin
                    if(count!=0) count<=count-1'b1;
                    else begin
                        shift[bit_index]<=rx_i;
                        if(DATA_ON_SAMPLE) data_o[bit_index]<=rx_i;
                        count<=BIT_CYCLES-1;
                        if(bit_index==7) state<=STOP;
                        else bit_index<=bit_index+1'b1;
                    end
                end
                STOP: begin
                    if(count!=0) count<=count-1'b1;
                    else begin
                        if(rx_i) begin
                            if(!DATA_ON_SAMPLE) data_o<=shift;
                            valid_o<=1;
                        end else framing_error_o<=1;
                        state<=IDLE;
                    end
                end
                default: state<=IDLE;
            endcase
        end
    endtask
    generate if(ASYNC_RESET) begin : g_async_reset
        always @(posedge clk or negedge reset_n) begin
            if(!reset_n) begin
                state<=IDLE;count<=0;bit_index<=0;shift<=0;
                data_o<=0;valid_o<=0;framing_error_o<=0;
            end else receive_step();
        end
    end else begin : g_sync_reset
        always @(posedge clk) begin
            if(!reset_n) begin
                state<=IDLE;count<=0;bit_index<=0;shift<=0;
                data_o<=0;valid_o<=0;framing_error_o<=0;
            end else receive_step();
        end
    end endgenerate
endmodule
