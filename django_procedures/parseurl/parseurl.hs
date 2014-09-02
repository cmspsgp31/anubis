{-# LANGUAGE DeriveGeneric, OverloadedStrings #-}
{-# OPTIONS -fno-warn-unused-do-bind #-}
module ParseUrl where

import qualified GHC.Generics as G
import qualified Data.Aeson as A
import qualified Data.ByteString as B
import qualified Data.ByteString.Lazy as BL
import qualified Data.Text as T
import qualified Data.Text.Encoding as E
import qualified Text.Parsec as P
import qualified Text.Parsec.Text as TP
import qualified Text.Parsec.Expr as PE

import Control.Monad.IO.Class (MonadIO, liftIO)
-- import Text.Parsec.Error (messageString, errorMessages)

import Foreign.C
import Control.Applicative
import Data.Maybe (isJust)
import Control.Monad.Identity (Identity)

data Search = Search
	{ field :: T.Text
	, args :: [T.Text]
	} deriving (Show, G.Generic)

instance A.FromJSON Search
instance A.ToJSON Search

data Expr = And { left :: Expr, right :: Expr }
	| Or { left :: Expr, right :: Expr }
	| Not Expr
	| Expr Search
	deriving (Show, G.Generic)

instance A.FromJSON Expr
instance A.ToJSON Expr

fieldParser :: TP.Parser T.Text
fieldParser = T.pack <$> P.many1 (P.letter <|> P.digit <|> P.oneOf "_-")

quotedArg :: TP.Parser T.Text
quotedArg = do
	arg <- T.pack <$> P.many1 (P.noneOf "$\"")
	escapedSeq "$\"" "\"" arg <|> escapedSeq "$$" "$" arg <|> return arg
	where escapedSeq escapeSeq char arg = do
			P.string escapeSeq
			next <- quotedArg
			return . T.concat $ [arg, char, next]

unquotedArg :: TP.Parser T.Text
unquotedArg = T.pack <$> P.many1 (P.letter <|> P.digit <|> P.oneOf "_-")

argParser :: TP.Parser T.Text
argParser = P.try (do
		P.char '"'
		arg <- quotedArg
		P.char '"'
		return arg)
	<|> unquotedArg

search :: TP.Parser Search
search = do
	key <- fieldParser
	P.char ','
	argList <- argParser `P.sepBy1` P.char ','
	return Search { field=key, args=argList }

parensExpr :: TP.Parser Expr -> TP.Parser Expr
parensExpr p = do
	P.char '('
	expr <- p
	P.char ')'
	return expr


expr :: TP.Parser Expr
expr = PE.buildExpressionParser table term

term :: TP.Parser Expr
term = parensExpr expr <|> fmap Expr search

table :: PE.OperatorTable T.Text () Identity Expr
table =
	[ [prefix "!" Not]
	, [binary "/" And PE.AssocLeft]
	, [binary "+" Or PE.AssocLeft]
	]

binary :: T.Text -> (Expr -> Expr -> Expr) -> PE.Assoc
	-> PE.Operator T.Text () Identity Expr
binary op f assoc = PE.Infix reserve assoc
	where
		reserve :: TP.Parser (Expr -> Expr -> Expr)
		reserve = (P.string . T.unpack) op >> return f

prefix :: T.Text -> (Expr -> Expr) -> PE.Operator T.Text () Identity Expr
prefix op f = PE.Prefix ((P.string . T.unpack) op >> return f)

-- singleExpr :: TP.Parser Expr
-- singleExpr = do
-- 	negation <- P.optionMaybe $ P.char '!'
-- 	expr <- Expr <$> search
-- 	if isJust negation
-- 		then return . Not $ expr
-- 		else return expr

-- chain :: TP.Parser a -> ([Expr] -> Expr) -> TP.Parser Expr
-- chain connector exprJoin = do
-- 	x <- elem'
-- 	connector
-- 	xs <- elem' `P.sepBy1` connector
-- 	return . exprJoin $ x : xs
-- 	where
-- 		elem' = P.try singleExpr <|> parensExpr

-- orChain :: TP.Parser Expr
-- orChain = chain (P.string "/ou/") Or

-- andChain :: TP.Parser Expr
-- andChain = chain (P.char '/') And

-- insideParensExpr :: TP.Parser Expr
-- insideParensExpr = P.try andChain <|> P.try orChain <|> singleExpr

-- fullExpr :: TP.Parser Expr
-- fullExpr = P.try singleExpr <|> P.try andChain <|> orChain
-- 	where
-- 		openBracket = do
-- 			P.char '/'
-- 			negation <- P.optionMaybe $ P.char '!'
-- 			P.char '*'
-- 			return . isJust $ negation
-- 		orChain = do
-- 			negation <- openBracket
-- 			x <- fullExpr
-- 			orOp
-- 			xs <- fullExpr `P.sepBy1` orOp
-- 			P.string "*/"
-- 			let expr = Or $ x : xs in if negation
-- 				then return . Not $ expr
-- 				else return expr
-- 		orOp = P.try (P.string "/ou/") <|> P.try (P.string "/ou") <|>
-- 			P.try (P.string "ou/") <|> P.string "ou"
-- 		andChain = do
-- 			negation <- openBracket
-- 			x <- fullExpr
-- 			P.char '/'
-- 			xs <- fullExpr `P.sepBy1` P.char '/'
-- 			P.string "*/"
-- 			let expr = And $ x : xs in if negation
-- 				then return . Not $ expr
-- 				else return expr

returnObj :: (A.ToJSON a, MonadIO m) => a -> m CString
returnObj = liftIO . flip B.useAsCString return . BL.toStrict . A.encode

foreign export ccall parseUrl :: CString -> IO CString
parseUrl :: CString -> IO CString
parseUrl cUrl = do
	url <- E.decodeUtf8 <$> B.packCString cUrl
	case P.parse expr "" url of
		Right result -> returnObj result
		Left err -> returnObj . show $ err

