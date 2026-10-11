# Scoped top-bar navigation treatment; two-frame normal/selected strips.
# Contract: installed HOI4 1.18.3 buttonstate.shader and buttonstate.fxh.
Includes = { "buttonstate.fxh" }
PixelShader = {
 Samplers = {
  MapTexture = {
   Index = 0
   MagFilter = "Point"
   MinFilter = "Point"
   MipFilter = "None"
   AddressU = "Clamp"
   AddressV = "Clamp"
  }
 }
}
VertexStruct VS_OUTPUT {
 float4 vPosition : PDX_POSITION;
 float2 vTexCoord : TEXCOORD0;
};
VertexShader = {
 MainCode VertexShader
 [[
  VS_OUTPUT main(const VS_INPUT v) {
   VS_OUTPUT Out;
   Out.vPosition = mul(WorldViewProjectionMatrix, float4(v.vPosition.xyz, 1));
   Out.vTexCoord = v.vTexCoord + Offset;
   return Out;
  }
 ]]
}
PixelShader = {
 MainCode PixelShaderUp
 [[
  float4 main(VS_OUTPUT v) : PDX_COLOR {
   return tex2D(MapTexture, v.vTexCoord) * Color;
  }
 ]]
 MainCode PixelShaderOver
 [[
  float4 main(VS_OUTPUT v) : PDX_COLOR {
   float4 OutColor = tex2D(MapTexture, v.vTexCoord);
   float2 Pixel = floor(float2(frac(v.vTexCoord.x * 2.0) * 55.0, v.vTexCoord.y * 41.0));
   // A crisp rim response; the artwork and face are not smeared or washed out.
   float Vertical = ((Pixel.x == 1.0 || Pixel.x == 53.0) && Pixel.y >= 3.0 && Pixel.y <= 37.0) ? 1.0 : 0.0;
   float Horizontal = ((Pixel.y == 1.0 || Pixel.y == 39.0) && Pixel.x >= 3.0 && Pixel.x <= 51.0) ? 1.0 : 0.0;
   OutColor.rgb = saturate(OutColor.rgb + float3(0.08, 0.18, 0.32) * max(Vertical, Horizontal));
   return OutColor * Color;
  }
 ]]
 MainCode PixelShaderDown
 [[
  float4 main(VS_OUTPUT v) : PDX_COLOR {
   float4 OutColor = tex2D(MapTexture, v.vTexCoord);
   OutColor.rgb *= 0.9;
   return OutColor * Color;
  }
 ]]
 MainCode PixelShaderDisable
 [[
  float4 main(VS_OUTPUT v) : PDX_COLOR {
   float4 OutColor = tex2D(MapTexture, v.vTexCoord);
   float Grey = dot(OutColor.rgb, float3(0.212671f, 0.715160f, 0.072169f));
   OutColor.rgb = float3(Grey, Grey, Grey) * 0.65;
   return OutColor * Color;
  }
 ]]
}
BlendState BlendState {
 BlendEnable = yes
 SourceBlend = "src_alpha"
 DestBlend = "inv_src_alpha"
}
Effect Up { VertexShader = "VertexShader" PixelShader = "PixelShaderUp" }
Effect Over { VertexShader = "VertexShader" PixelShader = "PixelShaderOver" }
Effect Down { VertexShader = "VertexShader" PixelShader = "PixelShaderDown" }
Effect Disable { VertexShader = "VertexShader" PixelShader = "PixelShaderDisable" }
