from decimal import Decimal
from typing import Tuple

from loguru import logger
from p2p.application import (Advertisement, Currency, Maker, Order,
                             OrderStatus, P2PAdapter, PaymentMethod, PeerOffer)
from p2p.application.foundation import Direction


class BinP2PAdapter(P2PAdapter):
    order_status_map = {OrderStatus.COMPLETED: 4}
    method_2_props = {
        "RUBfiatbalance": {
            "payType": "RUBfiatbalance",
            "identifier": "RUBfiatbalance",
            "iconUrlColor": "https://bin.bnbstatic.com/image/admin_mgs_image_upload/20201217/e46bf11d-5e87-4099-aed6-acf4fa51904b.png",
            "tradeMethodName": "BinancePay (RUB)",
            "tradeMethodShortName": "RUB fiat balance",
            "tradeMethodBgColor": "#D89F00",
        },
    }

    def decode_peer_offer(self, entry: dict) -> PeerOffer:
        try:
            methods = [PaymentMethod(x["identifier"]) for x in entry["payMethods"]]
        except Exception:
            logger.error(entry)
            raise
        return PeerOffer(
            offer_id=entry["advNo"],
            order_nb=entry["orderNumber"],
            direction=entry["tradeType"],
            asset=entry["asset"],
            amount=entry["amount"],
            fiat=entry["fiat"],
            price=entry["price"],
            payment_methods=methods,
            created=int(entry["createTime"]),
            participants=(entry["sellerNickname"], entry["buyerNickname"]),
        )

    def decode_my_advertisment(self, entry: dict) -> Advertisement:
        methods = [PaymentMethod(x["payType"]) for x in entry["tradeMethods"]]
        entry["maxSingleTransAmount"] = (
            entry["maxSingleTransAmount"]
            if entry["maxSingleTransAmount"] is not None
            else 999_999_999
        )
        entry["dynamicMaxSingleTransAmount"] = (
            entry["dynamicMaxSingleTransAmount"]
            if entry["dynamicMaxSingleTransAmount"] is not None
            else 999_999_999
        )
        return Advertisement(
            offer_id=entry["advNo"],
            direction=entry["tradeType"],
            asset=entry["asset"],
            fiat=entry["fiatUnit"],
            price=entry["price"],
            digits=entry["fiatScale"],
            time_limit=entry["payTimeLimit"],
            min_amount=entry["minSingleTransAmount"],
            max_amount=min(
                Decimal(entry["maxSingleTransAmount"]),
                Decimal(entry["dynamicMaxSingleTransAmount"]),
            ),
            payment_methods=methods,
            initial_amount=entry["initAmount"],
            price_type=entry["priceType"],
            auto_reply=entry["autoReplyMsg"],
            floating_ratio=entry["priceFloatingRatio"],
            remarks=entry["remarks"],
            buyer_reg_age=entry["buyerRegDaysLimit"],
        )

    def decode_order_book_entry(self, entry: dict) -> Order:
        try:
            c_k = entry["advertiser"]
            maker = Maker(
                user_no=c_k["userNo"],
                visible_name=c_k["nickName"],
                success_rate=c_k["monthFinishRate"],
                orders_count=c_k["monthOrderCount"],
                is_profi=False if c_k["userType"] == "user" else True,
            )
            c_k = entry["adv"]
            methods = [PaymentMethod(x["identifier"]) for x in c_k["tradeMethods"]]
            order = Order(
                offer_id=c_k["advNo"],
                maker=maker,
                direction=c_k["tradeType"],
                asset=c_k["asset"],
                fiat=c_k["fiatUnit"],
                price=c_k["price"],
                digits=c_k["fiatScale"],
                time_limit=c_k["payTimeLimit"],
                min_amount=c_k["minSingleTransAmount"],
                max_amount=min(
                    Decimal(c_k["maxSingleTransAmount"]),
                    Decimal(c_k["dynamicMaxSingleTransAmount"]),
                ),
                payment_methods=methods,
                initial_amount=c_k["initAmount"],
            )
        except Exception as ex:
            logger.error(f"{ex}, {entry}")
            raise
        return order

    def serialize_ads_update(self, ads: Advertisement) -> dict:
        stub = {
            "asset": ads.asset.upper(),
            "fiatUnit": ads.fiat.upper(),
            "priceType": 1,
            "fiatScale": ads.digits,
            "assetScale": 2,
            "priceScale": 2,
            "advNo": ads.offer_id,
            "autoReplyMsg": ads.auto_reply,
            "initAmount": str(ads.initial_amount),
            "payTimeLimit": ads.time_limit,
            "price": str(ads.price),
            "priceFloatingRatio": "",
            "minSingleTransAmount": str(ads.min_amount),
            "maxSingleTransAmount": str(ads.max_amount),
            "remarks": "",
            "tradeMethods": [
                self.serialise_payment_method(m, ads.direction)
                for m in ads.payment_methods
            ],
            "tradeType": ads.direction.value,
            "launchCountry": None,
            "buyerRegDaysLimit": ads.buyer_reg_age,
        }
        return stub

    def decode_payment_methods(self, method: dict) -> dict:
        keys = self.method_2_props["RUBfiatbalance"].keys()
        new_entry = {k: method[k] for k in keys if k != "payId"}
        new_entry["payId"] = method["id"]
        self.method_2_props[PaymentMethod(method["identifier"])] = new_entry
        return new_entry

    def serialize_ads_create(self, ads: Advertisement) -> dict:
        stub = self.serialize_ads_update(ads)
        del stub["advNo"]
        stub.update(
            {
                "buyerKycLimit": 1,
                "classify": "mass",
                "onlineDelayTime": 0,
                "onlineNow": True,
            }
        )
        return stub

    def serialise_payment_method(
        self, method: PaymentMethod, direction: Direction
    ) -> dict:
        method = [m for m in self.method_2_props if m.lower() == method.lower()][0]
        if direction == Direction.BUY:
            stub = {
                "payId": None,
                "payMethodId": "",
                "payAccount": None,
                "payBank": None,
                "paySubBank": None,
            }
            stub.update(self.method_2_props[method])
        else:
            try:
                stub = {
                    "identifier": method,
                    "payId": self.method_2_props[method],
                    "payType": None,
                    "payAccount": None,
                    "payBank": None,
                    "paySubBank": None,
                    "tradeMethodName": method,
                }
            except KeyError:
                logger.debug(self.method_2_props.keys())
                raise
        stub.update(self.method_2_props[method])
        return stub

    def serialize_ads_delete(self, ads: Advertisement) -> dict:
        stub = {"advNos": [ads.offer_id], "advStatus": 4}
        return stub

    def decode_ticker_entry(self, entry: dict) -> Tuple[Currency, Decimal]:
        return entry["symbol"], Decimal(entry["price"])

    def decode_balance_entry(self, entry: dict) -> Tuple[Currency, Decimal]:
        return entry["asset"], Decimal(entry["free"])
