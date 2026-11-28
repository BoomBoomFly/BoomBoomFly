// RGMII：上升沿低四位/RX_DV，下降沿高四位/RX_DV xor RX_ER。
// 输入为已移相的 RX 采样时钟；板测仍须确认 PHY 延迟与外部输入时序。
module rgmii_to_gmii (
    input wire rgmii_rx_clk_i,
    input wire [3:0] rgmii_rxd,
    input wire rgmii_rxdv,
    output wire [7:0] gmii_rxd,
    output wire gmii_rxdv,
    output wire gmii_rxer
);
    wire ctl_rise, ctl_fall;
    genvar lane;
    generate for(lane=0;lane<4;lane=lane+1)begin: lanes
        IDDR capture(.Q0(gmii_rxd[lane]),.Q1(gmii_rxd[lane+4]),
            .D(rgmii_rxd[lane]),.CLK(rgmii_rx_clk_i));
    end endgenerate
    IDDR control_capture(.Q0(ctl_rise),.Q1(ctl_fall),.D(rgmii_rxdv),.CLK(rgmii_rx_clk_i));
    assign gmii_rxdv=ctl_rise;
    assign gmii_rxer=ctl_rise^ctl_fall;
endmodule
