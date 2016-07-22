import numpy as np
import wx

import colors

# Font is a dict (easily serializable with JSON) with the following attributes:
#    data: string containing font data
#    name: human readable name
#    x_bits: number of bits to display
#    y_bytes: number of bytes per character
#
# template:
# Font = {
#    'data': ,
#    'name':"Default Atari Font",
#    'char_w': 8,
#    'char_h': 8,
#    }

A8DefaultFont = {
    'data': '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x18\x18\x18\x18\x00\x18\x00\x00fff\x00\x00\x00\x00\x00f\xffff\xfff\x00\x18>`<\x06|\x18\x00\x00fl\x180fF\x00\x1c6\x1c8of;\x00\x00\x18\x18\x18\x00\x00\x00\x00\x00\x0e\x1c\x18\x18\x1c\x0e\x00\x00p8\x18\x188p\x00\x00f<\xff<f\x00\x00\x00\x18\x18~\x18\x18\x00\x00\x00\x00\x00\x00\x00\x18\x180\x00\x00\x00~\x00\x00\x00\x00\x00\x00\x00\x00\x00\x18\x18\x00\x00\x06\x0c\x180`@\x00\x00<fnvf<\x00\x00\x188\x18\x18\x18~\x00\x00<f\x0c\x180~\x00\x00~\x0c\x18\x0cf<\x00\x00\x0c\x1c<l~\x0c\x00\x00~`|\x06f<\x00\x00<`|ff<\x00\x00~\x06\x0c\x1800\x00\x00<f<ff<\x00\x00<f>\x06\x0c8\x00\x00\x00\x18\x18\x00\x18\x18\x00\x00\x00\x18\x18\x00\x18\x180\x06\x0c\x180\x18\x0c\x06\x00\x00\x00~\x00\x00~\x00\x00`0\x18\x0c\x180`\x00\x00<f\x0c\x18\x00\x18\x00\x00<fnn`>\x00\x00\x18<ff~f\x00\x00|f|ff|\x00\x00<f``f<\x00\x00xlfflx\x00\x00~`|``~\x00\x00~`|```\x00\x00>``nf>\x00\x00ff~fff\x00\x00~\x18\x18\x18\x18~\x00\x00\x06\x06\x06\x06f<\x00\x00flxxlf\x00\x00`````~\x00\x00cw\x7fkcc\x00\x00fv~~nf\x00\x00<ffff<\x00\x00|ff|``\x00\x00<fffl6\x00\x00|ff|lf\x00\x00<`<\x06\x06<\x00\x00~\x18\x18\x18\x18\x18\x00\x00fffff~\x00\x00ffff<\x18\x00\x00cck\x7fwc\x00\x00ff<<ff\x00\x00ff<\x18\x18\x18\x00\x00~\x0c\x180`~\x00\x00\x1e\x18\x18\x18\x18\x1e\x00\x00@`0\x18\x0c\x06\x00\x00x\x18\x18\x18\x18x\x00\x00\x08\x1c6c\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x006\x7f\x7f>\x1c\x08\x00\x18\x18\x18\x1f\x1f\x18\x18\x18\x03\x03\x03\x03\x03\x03\x03\x03\x18\x18\x18\xf8\xf8\x00\x00\x00\x18\x18\x18\xf8\xf8\x18\x18\x18\x00\x00\x00\xf8\xf8\x18\x18\x18\x03\x07\x0e\x1c8p\xe0\xc0\xc0\xe0p8\x1c\x0e\x07\x03\x01\x03\x07\x0f\x1f?\x7f\xff\x00\x00\x00\x00\x0f\x0f\x0f\x0f\x80\xc0\xe0\xf0\xf8\xfc\xfe\xff\x0f\x0f\x0f\x0f\x00\x00\x00\x00\xf0\xf0\xf0\xf0\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00\xf0\xf0\xf0\xf0\x00\x1c\x1cww\x08\x1c\x00\x00\x00\x00\x1f\x1f\x18\x18\x18\x00\x00\x00\xff\xff\x00\x00\x00\x18\x18\x18\xff\xff\x18\x18\x18\x00\x00<~~~<\x00\x00\x00\x00\x00\xff\xff\xff\xff\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\x00\x00\x00\xff\xff\x18\x18\x18\x18\x18\x18\xff\xff\x00\x00\x00\xf0\xf0\xf0\xf0\xf0\xf0\xf0\xf0\x18\x18\x18\x1f\x1f\x00\x00\x00x`x`~\x18\x1e\x00\x00\x18<~\x18\x18\x18\x00\x00\x18\x18\x18~<\x18\x00\x00\x180~0\x18\x00\x00\x00\x18\x0c~\x0c\x18\x00\x00\x00\x18<~~<\x18\x00\x00\x00<\x06>f>\x00\x00``|ff|\x00\x00\x00<```<\x00\x00\x06\x06>ff>\x00\x00\x00<f~`<\x00\x00\x0e\x18>\x18\x18\x18\x00\x00\x00>ff>\x06|\x00``|fff\x00\x00\x18\x008\x18\x18<\x00\x00\x06\x00\x06\x06\x06\x06<\x00``lxlf\x00\x008\x18\x18\x18\x18<\x00\x00\x00f\x7f\x7fkc\x00\x00\x00|ffff\x00\x00\x00<fff<\x00\x00\x00|ff|``\x00\x00>ff>\x06\x06\x00\x00|f```\x00\x00\x00>`<\x06|\x00\x00\x18~\x18\x18\x18\x0e\x00\x00\x00ffff>\x00\x00\x00fff<\x18\x00\x00\x00ck\x7f>6\x00\x00\x00f<\x18<f\x00\x00\x00fff>\x0cx\x00\x00~\x0c\x180~\x00\x00\x18<~~\x18<\x00\x18\x18\x18\x18\x18\x18\x18\x18\x00~x|nf\x06\x00\x08\x188x8\x18\x08\x00\x10\x18\x1c\x1e\x1c\x18\x10\x00',
    'name': "8x8 Atari Default Font",
    'char_w': 8,
    'char_h': 8,
    }

A8ComputerFont = {
    'data': '\x00\x00\x00\x00\x00\x00\x00\x0088\x18\x18\x00\x18\x18\x00\xee\xeeDD\x00\x00\x00\x00f\xffff\xfff\x00\x00\x18>`<\x06|\x18\x00\x00fl\x180fF\x00\x1c6\x1c8of;\x00\x18\x18\x18\x00\x00\x00\x00\x00\x1e\x18\x18888>\x00x\x18\x18\x1c\x1c\x1c|\x00\x00f<\xff<f\x00\x00\x00\x18\x18~\x18\x18\x00\x00\x00\x00\x00\x00\x00\x18\x180\x00\x00\x00~\x00\x00\x00\x00\x00\x00\x00\x00\x00\x18\x18\x00\x03\x06\x0c\x180`@\x00\x7fccccc\x7f\x008\x18\x18\x18>>>\x00\x7f\x03\x03\x7f``\x7f\x00~\x06\x06\x7f\x07\x07\x7f\x00ppppw\x7f\x07\x00\x7f``\x7f\x03\x03\x7f\x00|l`\x7fcc\x7f\x00\x7f\x03\x03\x1f\x18\x18\x18\x00>66\x7fww\x7f\x00\x7fcc\x7f\x07\x07\x07\x00<<<\x00<<<\x00<<<\x00<<\x180\x06\x0c\x180\x18\x0c\x06\x00\x00~\x00\x00~\x00\x00\x00`0\x18\x0c\x180`\x00\x7fc\x03\x1f\x1c\x00\x1c\x00\x7fcooo`\x7f\x00?33\x7fsss\x00~ff\x7fgg\x7f\x00\x7fgg`cc\x7f\x00~ffwww\x7f\x00\x7f``\x7fpp\x7f\x00\x7f``\x7fppp\x00\x7fc`ogg\x7f\x00sss\x7fsss\x00\x7f\x1c\x1c\x1c\x1c\x1c\x7f\x00\x0c\x0c\x0c\x0e\x0en~\x00ffl\x7fggg\x00000ppp~\x00g\x7f\x7fwggg\x00gw\x7foggg\x00\x7fccggg\x7f\x00\x7fcc\x7fppp\x00\x7fccggg\x7f\x07~ff\x7fwww\x00\x7f`\x7f\x03ss\x7f\x00\x7f\x1c\x1c\x1c\x1c\x1c\x1c\x00gggggg\x7f\x00ggggo>\x1c\x00gggo\x7f\x7fg\x00sss>ggg\x00ggg\x7f\x1c\x1c\x1c\x00\x7ffl\x187g\x7f\x00\x1e\x18\x18\x18\x18\x18\x1e\x00@`0\x18\x0c\x06\x03\x00x\x18\x18\x18\x18\x18x\x00\x00\x08\x1c6c\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x006\x7f\x7f>\x1c\x08\x00\x18\x18\x18\x1f\x1f\x18\x18\x18\x03\x03\x03\x03\x03\x03\x03\x03\x18\x18\x18\xf8\xf8\x00\x00\x00\x18\x18\x18\xf8\xf8\x18\x18\x18\x00\x00\x00\xf8\xf8\x18\x18\x18\x03\x07\x0e\x1c8p\xe0\xc0\xc0\xe0p8\x1c\x0e\x07\x03\x01\x03\x07\x0f\x1f?\x7f\xff\x00\x00\x00\x00\x0f\x0f\x0f\x0f\x80\xc0\xe0\xf0\xf8\xfc\xfe\xff\x0f\x0f\x0f\x0f\x00\x00\x00\x00\xf0\xf0\xf0\xf0\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00\xf0\xf0\xf0\xf0\x00\x1c\x1cww\x08\x1c\x00\x00\x00\x00\x1f\x1f\x18\x18\x18\x00\x00\x00\xff\xff\x00\x00\x00\x18\x18\x18\xff\xff\x18\x18\x18\x00\x00<~~~<\x00\x00\x00\x00\x00\xff\xff\xff\xff\xc0\xc0\xc0\xc0\xc0\xc0\xc0\xc0\x00\x00\x00\xff\xff\x18\x18\x18\x18\x18\x18\xff\xff\x00\x00\x00\xf0\xf0\xf0\xf0\xf0\xf0\xf0\xf0\x18\x18\x18\x1f\x1f\x00\x00\x00x`x`~\x18\x1e\x00\x00\x18<~\x18\x18\x18\x00\x00\x18\x18\x18~<\x18\x00\x00\x180~0\x18\x00\x00\x00\x18\x0c~\x0c\x18\x00\x00\x00\x18<~~<\x18\x00\x00\x00>\x02~v~\x00```~fn~\x00\x00\x00>20:>\x00\x06\x06\x06~fv~\x00\x00\x00~f~p~\x00\x00\x1e\x18>\x18\x1c\x1c\x00\x00\x00~fv~\x06~```~fvv\x00\x00\x18\x00\x18\x18\x1c\x1c\x00\x00\x0c\x00\x0c\x0c\x0e\x0e~\x00006|vw\x00\x00\x18\x18\x18\x1e\x1e\x1e\x00\x00\x00f\x7f\x7fkc\x00\x00\x00|fvvv\x00\x00\x00~fvv~\x00\x00\x00~fv~``\x00\x00~fn~\x06\x06\x00\x00>0888\x00\x00\x00> >\x0e~\x00\x00\x18~\x18\x1c\x1c\x1c\x00\x00\x00ffnn~\x00\x00\x00fnn>\x1c\x00\x00\x00ck\x7f>6\x00\x00\x00f>\x18>n\x00\x00\x00fff~\x0e~\x00\x00~\x1c\x186~\x00\x00\x18<~~\x18<\x00\x18\x18\x18\x18\x18\x18\x18\x18\x00~x|nf\x06\x00\x08\x188x8\x18\x08\x00\x10\x18\x1c\x1e\x1c\x18\x10\x00',
    'name': "8x8 Atari Custom Computer Font",
    'char_w': 8,
    'char_h': 8,
    }

A2ComputerFont = {
    'data': "8DT\\X@<\x00\x10(DD|DD\x00xDDxDDx\x008D@@@D8\x00xDDDDDx\x00|@@x@@|\x00|@@x@@@\x00<@@@LD<\x00DDD|DDD\x008\x10\x10\x10\x10\x108\x00\x04\x04\x04\x04DD8\x00DHP`PHD\x00@@@@@@~\x00DlTTDDD\x00DDdTLDD\x008DDDDD8\x00xDDx@@@\x008DDDTH4\x00xDDxPHD\x008D@8\x04D8\x00|\x10\x10\x10\x10\x10\x10\x00DDDDDD8\x00DDDDD(\x10\x00DDTTTlD\x00DD(\x10(DD\x00DD(\x10\x10\x10\x10\x00|\x04\x08\x10 @|\x00|`````|\x00\x00@ \x10\x08\x04\x00\x00|\x0c\x0c\x0c\x0c\x0c|\x00\x10(D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x10\x10\x10\x10\x00\x10\x00(((\x00\x00\x00\x00\x00((|(|((\x00\x10<P8\x14x\x10\x00`d\x08\x10 L\x0c\x00 PP TH4\x00\x10\x10\x10\x00\x00\x00\x00\x00\x08\x10   \x10\x08\x00 \x10\x08\x08\x08\x10 \x00\x10T8\x108T\x10\x00\x00\x10\x10|\x10\x10\x00\x00\x00\x00\x00\x00\x00\x08\x08\x10\x00\x00\x00|\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x04\x08\x10 @\x00\x008DLTdD8\x00\x100\x10\x10\x10\x108\x008D\x04\x18 @|\x00|\x04\x08\x18\x04D8\x00\x08\x18(H|\x08\x08\x00|@x\x04\x04D8\x00\x1c @xDD8\x00|\x04\x08\x10   \x008DD8DD8\x008DD<\x04\x08p\x00\x00\x00\x10\x00\x00\x10\x00\x00\x00\x00\x00\x10\x00\x10\x10 \x08\x10 @ \x10\x08\x00\x00\x00|\x00|\x00\x00\x00 \x10\x08\x04\x08\x10 \x008D\x08\x10\x10\x00\x10\x008DT\\X@<\x00\x10(DD|DD\x00xDDxDDx\x008D@@@D8\x00xDDDDDx\x00|@@x@@|\x00|@@x@@@\x00<@@@LD<\x00DDD|DDD\x008\x10\x10\x10\x10\x108\x00\x04\x04\x04\x04DD8\x00DHP`PHD\x00@@@@@@~\x00DlTTDDD\x00DDdTLDD\x008DDDDD8\x00xDDx@@@\x008DDDTH4\x00xDDxPHD\x008D@8\x04D8\x00|\x10\x10\x10\x10\x10\x10\x00DDDDDD8\x00DDDDD(\x10\x00DDTTTlD\x00DD(\x10(DD\x00DD(\x10\x10\x10\x10\x00|\x04\x08\x10 @|\x00|`````|\x00\x00@ \x10\x08\x04\x00\x00|\x0c\x0c\x0c\x0c\x0c|\x00\x10(D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\xff\x00 \x10\x08\x00\x00\x00\x00\x00\x00\x008\x04<D<\x00@@XdDDx\x00\x00\x008D@D8\x00\x04\x044LDD<\x00\x00\x008D|@<\x00\x18$ p   \x00\x00\x004LD<\x04x@@XdDDD\x00\x10\x000\x10\x10\x108\x00\x04\x00\x04\x04\x04\x04D8@@HP`PH\x000\x10\x10\x10\x10\x108\x00\x00\x00hTTTT\x00\x00\x00XdDDD\x00\x00\x008DDD8\x00\x00\x00xDDx@@\x00\x00<DD<\x04\x04\x00\x00Xd@@@\x00\x00\x00<@8\x04x\x00  x  $\x18\x00\x00\x00DDDL4\x00\x00\x00DD((\x10\x00\x00\x00TTTT(\x00\x00\x00D(\x10(D\x00\x00\x00DDD<\x04x\x00\x00|\x08\x10 |\x00\x10  @  \x10\x00\x10\x10\x10\x10\x10\x10\x10\x00\x10\x08\x08\x04\x08\x08\x10\x00\x00d\x98\x00\x00\x00\x00\x00\x00T(T(T\x00\x00",
    'name': "7x8 Apple ][ Font",
    'char_w': 7,
    'char_h': 8,
    'blink': True,
    }


class AnticFont(object):
    def __init__(self, machine, font_data, font_renderer, playfield_colors, reverse=False):
        self.use_blinking = font_data.get('blink', False)
        self.char_w = font_renderer.char_bit_width
        self.char_h = font_renderer.char_bit_height
        self.scale_w = font_renderer.scale_width
        self.scale_h = font_renderer.scale_height
        
        self.set_colors(machine, playfield_colors)
        self.set_fonts(machine, font_data, font_renderer, reverse)
    
    def set_colors(self, machine, playfield_colors):
        fg, bg = colors.gr0_colors(playfield_colors)
        conv = machine.get_color_converter()
        fg = conv(fg)
        bg = conv(bg)
        self.normal_gr0_colors = [fg, bg]
        self.highlight_gr0_colors = machine.get_blended_color_registers(self.normal_gr0_colors, machine.highlight_color)
        self.match_gr0_colors = machine.get_blended_color_registers(self.normal_gr0_colors, machine.match_background_color)
        self.comment_gr0_colors = machine.get_blended_color_registers(self.normal_gr0_colors, machine.comment_background_color)
        self.data_gr0_colors = machine.get_dimmed_color_registers(self.normal_gr0_colors, machine.background_color, machine.data_color)
    
    def set_fonts(self, machine, font_data, font_renderer, reverse):
        if 'np_data' in font_data:
            bytes = font_data['np_data']
        else:
            bytes = np.fromstring(font_data['data'], dtype=np.uint8)
        bits = np.unpackbits(bytes)
        bits = bits.reshape((-1, 8, 8))
        
        self.normal_font = font_renderer.bits_to_font(bits, machine.color_registers, self.normal_gr0_colors, reverse)
        self.highlight_font = font_renderer.bits_to_font(bits, machine.color_registers_highlight, self.highlight_gr0_colors, reverse)
        self.data_font = font_renderer.bits_to_font(bits, machine.color_registers_data, self.data_gr0_colors, reverse)
        self.match_font = font_renderer.bits_to_font(bits, machine.color_registers_match, self.match_gr0_colors, reverse)
        self.comment_font = font_renderer.bits_to_font(bits, machine.color_registers_comment, self.comment_gr0_colors, reverse)
    
    def get_height(self, zoom):
        return self.char_h * self.scale_h * zoom
    
    def get_image(self, char_index, zoom, highlight=False):
        f = self.highlight_font if highlight else self.normal_font
        array = f[char_index]
        w = self.char_w
        h = self.char_h
        image = wx.EmptyImage(w, h)
        image.SetData(array.tostring())
        w *= self.scale_w * zoom
        h *= self.scale_h * zoom
        image.Rescale(w, h)
        bmp = wx.BitmapFromImage(image)
        return bmp
