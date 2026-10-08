# Production equipment only. The slate obsolete overlay leaves the three-pixel
# native button rim visible so the engine's Over/Down state can reach it.
# Card alpha encodes only the rim mask: 255 at the rim, 254 on the face.
# All four states restore full opacity before applying the engine Color.
# Interface contract: installed HOI4 1.18.3.0.7709 buttonstate.shader/.fxh.
Includes = { "buttonstate.fxh" }

PixelShader = {
	Samplers = {
		MapTexture = {
			Index = 0
			MagFilter = "Linear"
			MinFilter = "Linear"
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
			float4 OutColor = tex2D(MapTexture, v.vTexCoord);
			OutColor.a = 1.0;
			return OutColor * Color;
		}
	]]
	MainCode PixelShaderOver
	[[
		float4 main(VS_OUTPUT v) : PDX_COLOR {
			float4 OutColor = tex2D(MapTexture, v.vTexCoord);
			// The same three-pixel blue rim on current and outdated equipment.
			// Leave the face RGB untouched; filtering interpolates the rim edge.
			float Rim = saturate((OutColor.a - 254.0 / 255.0) * 255.0);
			OutColor.rgb = saturate(OutColor.rgb + float3(0.20, 0.40, 0.70) * Rim);
			OutColor.a = 1.0;
			return OutColor * Color;
		}
	]]
	MainCode PixelShaderDown
	[[
		float4 main(VS_OUTPUT v) : PDX_COLOR {
			float4 OutColor = tex2D(MapTexture, v.vTexCoord);
			OutColor.a = 1.0;
			OutColor *= Color;
			float vTime = 0.9 - saturate((Time - AnimationTime) * 16);
			vTime = 0.9 * 0.9 - vTime * vTime;
			OutColor.rgb -= (0.5 + OutColor.rgb) * 0.15 * vTime;
			return OutColor;
		}
	]]
	MainCode PixelShaderDisable
	[[
		float4 main(VS_OUTPUT v) : PDX_COLOR {
			float4 OutColor = tex2D(MapTexture, v.vTexCoord);
			float Grey = dot(OutColor.rgb, float3(0.212671f, 0.715160f, 0.072169f));
			OutColor.rgb = float3(Grey, Grey, Grey);
			OutColor.a = 1.0;
			return OutColor * Color;
		}
	]]
}

BlendState BlendState {
	BlendEnable = yes
	SourceBlend = "src_alpha"
	DestBlend = "inv_src_alpha"
}
Effect Up {
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderUp"
}
Effect Over {
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderOver"
}
Effect Down {
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderDown"
}
Effect Disable {
	VertexShader = "VertexShader"
	PixelShader = "PixelShaderDisable"
}
