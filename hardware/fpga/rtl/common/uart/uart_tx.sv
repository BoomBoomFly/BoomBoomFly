// Integrated UART support: uart_tx.sv
`timescale 1ns/1ps

module uart_tx #(
    parameter integer CLK_HZ = 50_000_000,
    parameter integer BAUD = 115200
) (
    input  wire       clk_i,
    input  wire       rst_i,
    input  wire [7:0] data_i,
    input  wire       start_i,
    output reg        tx_o,
    output reg        busy_o
);
    localparam integer CLKS_PER_BIT = CLK_HZ / BAUD;
    localparam [1:0] ST_IDLE = 2'd0;
    localparam [1:0] ST_START = 2'd1;
    localparam [1:0] ST_DATA = 2'd2;
    localparam [1:0] ST_STOP = 2'd3;

    reg [1:0] state;
    reg [31:0] count;
    reg [2:0] bit_index;
    reg [7:0] data_reg;

    always @(posedge clk_i) begin
        if (rst_i) begin
            state <= ST_IDLE;
            count <= 32'd0;
            bit_index <= 3'd0;
            data_reg <= 8'd0;
            tx_o <= 1'b1;
            busy_o <= 1'b0;
        end else begin
            case (state)
                ST_IDLE: begin
                    tx_o <= 1'b1;
                    busy_o <= 1'b0;
                    if (start_i) begin
                        data_reg <= data_i;
                        bit_index <= 3'd0;
                        count <= CLKS_PER_BIT - 1;
                        tx_o <= 1'b0;
                        busy_o <= 1'b1;
                        state <= ST_START;
                    end
                end

                ST_START: begin
                    busy_o <= 1'b1;
                    if (count == 0) begin
                        tx_o <= data_reg[0];
                        count <= CLKS_PER_BIT - 1;
                        state <= ST_DATA;
                    end else begin
                        count <= count - 1'b1;
                    end
                end

                ST_DATA: begin
                    busy_o <= 1'b1;
                    if (count == 0) begin
                        count <= CLKS_PER_BIT - 1;
                        if (bit_index == 3'd7) begin
                            tx_o <= 1'b1;
                            state <= ST_STOP;
                        end else begin
                            bit_index <= bit_index + 1'b1;
                            tx_o <= data_reg[bit_index + 1'b1];
                        end
                    end else begin
                        count <= count - 1'b1;
                    end
                end

                ST_STOP: begin
                    busy_o <= 1'b1;
                    if (count == 0) begin
                        tx_o <= 1'b1;
                        busy_o <= 1'b0;
                        state <= ST_IDLE;
                    end else begin
                        count <= count - 1'b1;
                    end
                end

                default: state <= ST_IDLE;
            endcase
        end
    end
endmodule
