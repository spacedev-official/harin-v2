import aiohttp


class Tracking:
    def __init__(self, company: str = None, delivery_code: int = None):
        self.company = company
        self.delivery_code = delivery_code
        self.company_list = [
            {
                "id": "de.dhl",
                "name": "DHL",
                "tel": "+8215880001"
            },
            {
                "id": "kr.chunilps",
                "name": "천일택배",
                "tel": "+8218776606"
            },
            {
                "id": "kr.cjlogistics",
                "name": "CJ대한통운",
                "tel": "+8215881255"
            },
            {
                "id": "kr.cupost",
                "name": "CU 편의점택배",
                "tel": "+8215771287"
            },
            {
                "id": "kr.cvsnet",
                "name": "GS Postbox 택배",
                "tel": "+8215771287"
            },
            {
                "id": "kr.cway",
                "name": "CWAY (Woori Express)",
                "tel": "+8215884899"
            },
            {
                "id": "kr.daesin",
                "name": "대신택배",
                "tel": "+82314620100"
            },
            {
                "id": "kr.epost",
                "name": "우체국 택배",
                "tel": "+8215881300"
            },
            {
                "id": "kr.hanips",
                "name": "한의사랑택배",
                "tel": "+8216001055"
            },
            {
                "id": "kr.hanjin",
                "name": "한진택배",
                "tel": "+8215880011"
            },
            {
                "id": "kr.hdexp",
                "name": "합동택배",
                "tel": "+8218993392"
            },
            {
                "id": "kr.homepick",
                "name": "홈픽",
                "tel": "+8218000987"
            },
            {
                "id": "kr.honamlogis",
                "name": "한서호남택배",
                "tel": "+8218770572"
            },
            {
                "id": "kr.ilyanglogis",
                "name": "일양로지스",
                "tel": "+8215880002"
            },
            {
                "id": "kr.kdexp",
                "name": "경동택배",
                "tel": "+8218995368"
            },
            {
                "id": "kr.kunyoung",
                "name": "건영택배",
                "tel": "+82533543001"
            },
            {
                "id": "kr.logen",
                "name": "로젠택배",
                "tel": "+8215889988"
            },
            {
                "id": "kr.lotte",
                "name": "롯데택배",
                "tel": "+8215882121"
            },
            {
                "id": "kr.slx",
                "name": "SLX",
                "tel": "+82316375400"
            },
            {
                "id": "kr.swgexp",
                "name": "성원글로벌카고",
                "tel": "+82327469984"
            },
            {
                "id": "un.upu.ems",
                "name": "EMS"
            },
            {
                "id": "us.fedex",
                "name": "Fedex"
            },
            {
                "id": "us.ups",
                "name": "UPS"
            },
            {
                "id": "us.usps",
                "name": "USPS"
            }
        ]
        self.url = "https://apis.tracker.delivery/carriers/{carrier_id}/tracks/{track_id}"
        self.data:dict = {}
        super().__init__()

    async def get_info(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=self.url.format(carrier_id=self.company, track_id=self.delivery_code)) as resp:
                if resp.status == 200:
                    return {"status": resp.status, "message": "조회완료.", "data": await resp.json()}
                else:
                    return {"status": resp.status, "message": "운송장이 등록되어있지않거나 운송장번호와 일치하지않는 배송사입니다.", "data": None}

    def get_company_list(self):
        return self.company_list
