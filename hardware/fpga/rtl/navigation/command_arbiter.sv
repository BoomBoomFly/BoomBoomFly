// ==================== command_arbiter.sv ====================
`timescale 1ns/1ps
// 单一通信入口的手动/自动仲裁。模式切换先停车，自动租约超时后必须重新启用。
module command_arbiter #(
    parameter integer LEASE_CYCLES=10000000,
    parameter integer ALLOW_LEGACY_AUTO=1
)(
    input wire clk,reset_n,
    input wire manual_valid_i,
    input wire [47:0] manual_velocity_i,
    input wire link_down_i,mode_valid_i,auto_enable_i,
    input wire planner_valid_i,planner_scan_valid_i,planner_fault_i,
    input wire [47:0] planner_velocity_i,
    input wire [63:0] now_us_i,
    input wire task_accepted_i,task_done_i,task_fault_i,
    input wire [7:0] task_mode_i,task_flags_i,
    input wire [63:0] task_expiry_us_i,
    input wire navigation_valid_i,input wire [47:0] navigation_velocity_i,
    input wire cancel_i,
    output wire navigation_cancel_o,
    output reg auto_mode_o,
    output wire valid_o,link_down_o,
    output wire [47:0] velocity_o
);
    localparam integer AGE_W=LEASE_CYCLES<2 ? 1 : $clog2(LEASE_CYCLES+1);
    reg [AGE_W-1:0] age;
    reg owned;
    reg task_owned;
    reg [7:0] task_mode,task_flags;
    reg [63:0] task_expiry;
    wire task_expired=task_owned && now_us_i>=task_expiry;
    wire task_link_stop=task_owned && link_down_i && task_mode!=3 && !task_flags[0];
    wire task_cancel=task_owned && (manual_valid_i || mode_valid_i || cancel_i===1'b1 ||
        task_fault_i===1'b1 || task_expired || task_link_stop);
    assign navigation_cancel_o=task_cancel;
    wire lease_expired=owned && !task_owned && age>=LEASE_CYCLES-1 && !manual_valid_i && !mode_valid_i;
    wire mode_change=mode_valid_i && (!auto_enable_i || !auto_mode_o);
    wire manual_takeover=manual_valid_i && auto_mode_o;
    wire stop_now=mode_change || manual_takeover || lease_expired || task_cancel || (task_owned && task_done_i===1'b1);
    assign link_down_o=task_owned ? (task_cancel || task_fault_i===1'b1) :
        (link_down_i || (auto_mode_o && (!planner_scan_valid_i || planner_fault_i || lease_expired)));
    assign valid_o=stop_now || (task_owned ? navigation_valid_i : (auto_mode_o ? planner_valid_i : manual_valid_i));
    assign velocity_o=(stop_now || link_down_o) ? 48'd0 :
        task_owned ? navigation_velocity_i : (auto_mode_o ? planner_velocity_i : manual_velocity_i);
    always @(posedge clk or negedge reset_n) begin
        if(!reset_n)begin auto_mode_o<=0;owned<=0;age<=0;end
        else if(task_accepted_i===1'b1 || link_down_i || lease_expired)begin auto_mode_o<=0;owned<=0;age<=0;end
        else if(mode_valid_i)begin auto_mode_o<=auto_enable_i && ALLOW_LEGACY_AUTO!=0;owned<=auto_enable_i && ALLOW_LEGACY_AUTO!=0;age<=0;end
        else if(manual_valid_i)begin auto_mode_o<=0;owned<=1;age<=0;end
        else if(owned)age<=age+1'b1;
    end
    always @(posedge clk or negedge reset_n)begin
        if(!reset_n)begin task_owned<=0;task_mode<=0;task_flags<=0;task_expiry<=0;end
        else if(task_cancel)task_owned<=0;
        else if(task_accepted_i===1'b1)begin
            task_owned<=1;task_mode<=task_mode_i;task_flags<=task_flags_i;task_expiry<=task_expiry_us_i;
        end
        else if(task_done_i===1'b1)task_owned<=0;
    end
endmodule
